from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, or_
from auth.database import get_async_session, User
from models.models import chat, task, message
from fastapi_users import FastAPIUsers
from auth.auth import auth_backend
from auth.manager import get_user_manager

router = APIRouter(
    prefix="/chats",
    tags=["chats"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Функція для отримання імені користувача за його ID
async def get_user_name_by_id(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    return user.username if user else "Unknown"

# Створення чату з власником задачі
@router.post("/with-owner/{task_id}")
async def create_chat_with_owner(
    task_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    task_row = result.mappings().first()

    if not task_row:
        raise HTTPException(status_code=404, detail="Task not found")

    customer_id = task_row["customer_id"]
    executor_id = current_user.id

    if customer_id == executor_id:
        raise HTTPException(status_code=400, detail="Cannot create chat with yourself")

    existing_chat = await session.execute(
        select(chat.c.id).where(
            or_(
                (chat.c.user1_id == customer_id) & (chat.c.user2_id == executor_id),
                (chat.c.user1_id == executor_id) & (chat.c.user2_id == customer_id)
            )
        )
    )
    chat_row = existing_chat.first()
    if chat_row:
        return {"chat_id": chat_row[0]}

    new_chat = await session.execute(
        insert(chat).values(
            user1_id=customer_id,
            user2_id=executor_id,
            task_id=task_id,
            created_at=datetime.utcnow()
        ).returning(chat.c.id)
    )
    await session.commit()

    chat_id = new_chat.scalar()
    return {"chat_id": chat_id}

# Отримання всіх чатів користувача
@router.get("/")
async def get_user_chats(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    result = await session.execute(
        select(chat).where(
            or_(
                chat.c.user1_id == current_user.id,
                chat.c.user2_id == current_user.id
            )
        )
    )
    chats = result.fetchall()

    if not chats:
        raise HTTPException(status_code=404, detail="No chats found")

    chats_data = []
    for chat_row in chats:
        partner_id = chat_row.user1_id if chat_row.user2_id == current_user.id else chat_row.user2_id
        partner_name = await get_user_name_by_id(partner_id, session)
        chats_data.append({
            "id": chat_row.id,
            "partner_name": partner_name,
        })

    return chats_data

# Отримання конкретного чату за ID
@router.get("/{chat_id}")
async def get_chat_by_id(
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    result = await session.execute(
        select(chat).where(chat.c.id == chat_id)
    )
    chat_row = result.mappings().first()

    if not chat_row:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Access denied")

    partner_id = chat_row["user1_id"] if chat_row["user2_id"] == current_user.id else chat_row["user2_id"]
    partner_name = await get_user_name_by_id(partner_id, session)

    return {
        "id": chat_row["id"],
        "partner_name": partner_name
    }
@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Текст повідомлення не може бути порожнім")

    # Перевірка чи чат існує і чи має до нього доступ поточний користувач
    result = await session.execute(
        select(chat).where(chat.c.id == chat_id)
    )
    chat_row = result.mappings().first()

    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Немає доступу до чату")

    # Додати повідомлення
    new_msg = await session.execute(
        insert(message).values(
            chat_id=chat_id,
            sender_id=current_user.id,
            content=text,  # Використовуємо "content" замість "text"
            created_at=datetime.utcnow()
        ).returning(
            message.c.id, message.c.content, message.c.sender_id, message.c.created_at
        )
    )
    await session.commit()
    msg = new_msg.mappings().first()

    return {
        "id": msg["id"],
        "text": msg["content"],  # Використовуємо "content" тут також
        "sender": "me",  # на фронті в тебе є перевірка message.sender === 'me'
        "created_at": msg["created_at"].isoformat()
    }

@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: int,
    limit: int = 20,  # За замовчуванням підгружаємо 20 повідомлень
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    # Перевірка чи чат існує і чи має до нього доступ поточний користувач
    result = await session.execute(
        select(chat).where(chat.c.id == chat_id)
    )
    chat_row = result.mappings().first()

    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Немає доступу до чату")

    # Отримання повідомлень чату з обмеженням на кількість
    result = await session.execute(
        select(message).where(message.c.chat_id == chat_id)
        .order_by(message.c.created_at.asc())
        .limit(limit)
    )
    messages = result.fetchall()

    if not messages:
        return []  # Повертаємо порожній список, якщо немає повідомлень

    messages_data = []
    for msg in messages:
        sender = "me" if msg.sender_id == current_user.id else "other"
        messages_data.append({
            "id": msg.id,
            "text": msg.content,
            "sender": sender,
            "created_at": msg.created_at.isoformat()
        })

    return messages_data
