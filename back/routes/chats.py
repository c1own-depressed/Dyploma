from datetime import datetime
from typing import List, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, or_, update, func, desc
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

async def get_user_name_by_id(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user_db = result.scalars().first() # Змінено user на user_db для уникнення конфлікту
    return user_db.username if user_db else "Unknown"

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


# ОНОВЛЕНИЙ ЕНДПОІНТ ДЛЯ ОТРИМАННЯ ВСІХ ЧАТІВ З РОЗШИРЕНОЮ ІНФОРМАЦІЄЮ
@router.get("/", response_model=List[Dict[str, Any]])  # Важливо додати response_model для Swagger
async def get_user_chats(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(fastapi_users.current_user()),
):
    user_chats_select = await session.execute(
        select(chat.c.id, chat.c.user1_id, chat.c.user2_id)  # Вибираємо потрібні поля
        .where(
            or_(
                chat.c.user1_id == current_user.id,
                chat.c.user2_id == current_user.id
            )
        )
        .order_by(chat.c.created_at.desc())  # Можна сортувати за останнім повідомленням пізніше
    )
    user_chats = user_chats_select.mappings().fetchall()  # .fetchall() та .mappings()

    if not user_chats:
        # Повертаємо порожній список замість HTTPException, якщо це нормальна ситуація
        return []

    chats_data = []
    for chat_item in user_chats:  # Змінено змінну для уникнення конфлікту
        partner_id = chat_item["user1_id"] if chat_item["user2_id"] == current_user.id else chat_item["user2_id"]
        partner_name = await get_user_name_by_id(partner_id, session)

        # Отримати останнє повідомлення
        last_message_select = await session.execute(
            select(message.c.content, message.c.created_at, message.c.sender_id, message.c.is_read)
            .where(message.c.chat_id == chat_item["id"])
            .order_by(message.c.created_at.desc())
            .limit(1)
        )
        last_msg_obj = last_message_select.mappings().first()

        last_message_snippet = None
        last_message_timestamp = None
        last_message_sent_by_me = None
        is_last_message_read_by_partner = None

        if last_msg_obj:
            last_message_snippet = last_msg_obj["content"][:40] + "..." if len(last_msg_obj["content"]) > 40 else \
            last_msg_obj["content"]  # Обрізка
            last_message_timestamp = last_msg_obj["created_at"].isoformat()
            last_message_sent_by_me = (last_msg_obj["sender_id"] == current_user.id)
            if last_message_sent_by_me:
                is_last_message_read_by_partner = last_msg_obj["is_read"]
            # Поле is_read для повідомлення від партнера показує, чи прочитав його ПОТОЧНИЙ користувач.
            # Це не те саме, що is_last_message_read_by_partner.

        # Отримати кількість непрочитаних повідомлень від партнера
        unread_count_select = await session.execute(
            select(func.count(message.c.id))
            .where(
                (message.c.chat_id == chat_item["id"]) &
                (message.c.sender_id == partner_id) &
                (message.c.is_read == False)  # Повідомлення від партнера, які поточний юзер не прочитав
            )
        )
        unread_messages_count = unread_count_select.scalar_one_or_none() or 0

        chats_data.append({
            "id": chat_item["id"],
            "partner_name": partner_name,
            "last_message_snippet": last_message_snippet,
            "last_message_timestamp": last_message_timestamp,
            "last_message_sent_by_me": last_message_sent_by_me,
            "is_last_message_read_by_partner": is_last_message_read_by_partner,
            "unread_messages_count": unread_messages_count,
        })

    # Додаткове сортування: чати з останніми повідомленнями вгорі
    # Потрібно обережно обробляти None для last_message_timestamp
    chats_data.sort(
        key=lambda x: datetime.fromisoformat(x["last_message_timestamp"].replace("Z", "+00:00")) if x[
            "last_message_timestamp"] else datetime.min.replace(tzinfo=None),
        reverse=True
    )

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
async def send_message_endpoint( # Перейменовано функцію для уникнення конфлікту з ім'ям моделі
    chat_id: int,
    payload: Dict[str, str], # Краще використовувати Pydantic модель
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Текст повідомлення не може бути порожнім")

    result = await session.execute(
        select(chat).where(chat.c.id == chat_id)
    )
    chat_row = result.mappings().first()

    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Немає доступу до чату")

    new_msg_stmt = insert(message).values(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=text,
        created_at=datetime.utcnow(),
        is_read=False # Нові повідомлення завжди не прочитані
    ).returning(
        message.c.id,
        message.c.content,
        message.c.sender_id,
        message.c.created_at,
        message.c.is_read # Повертаємо is_read
    )
    new_msg_result = await session.execute(new_msg_stmt)
    await session.commit()
    msg = new_msg_result.mappings().first()

    if not msg:
        raise HTTPException(status_code=500, detail="Не вдалося створити повідомлення")

    return {
        "id": msg["id"],
        "text": msg["content"],
        "sender": "me", # Бо відправник - поточний користувач
        "created_at": msg["created_at"].isoformat(),
        "is_read": msg["is_read"]
    }

@router.get("/{chat_id}/messages", response_model=List[Dict[str, Any]]) # Додано response_model
async def get_messages_endpoint( # Перейменовано функцію
    chat_id: int,
    page: int = Query(1, ge=1), # Пагінація як на фронтенді
    page_size: int = Query(20, ge=1, le=100), # Розмір сторінки
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    result = await session.execute(
        select(chat).where(chat.c.id == chat_id)
    )
    chat_row = result.mappings().first()

    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Немає доступу до чату")

    offset = (page - 1) * page_size

    # Отримуємо повідомлення, сортуючи від найстаріших до найновіших для даної сторінки
    # Фронтенд очікує, що старіші повідомлення йдуть першими при дозавантаженні
    # Для першого завантаження (page=1) можна було б сортувати desc і потім reverse на фронті
    # Або завжди asc і фронтенд правильно їх додає.
    # Залишимо asc, як у вас було на фронті.
    messages_query = (
        select(message.c.id, message.c.content, message.c.sender_id, message.c.created_at, message.c.is_read)
        .where(message.c.chat_id == chat_id)
        .order_by(message.c.created_at.asc()) # Старіші спочатку
        .offset(offset)
        .limit(page_size)
    )
    db_messages_result = await session.execute(messages_query)
    db_messages = db_messages_result.fetchall() # .fetchall() для SQLAlchemy 2.0+

    if not db_messages:
        return []

    messages_data = []
    for msg_row in db_messages: # msg_row - це Row об'єкт
        sender_type = "me" if msg_row.sender_id == current_user.id else "other"
        messages_data.append({
            "id": msg_row.id,
            "text": msg_row.content,
            "sender": sender_type,
            "created_at": msg_row.created_at.isoformat(),
            "is_read": msg_row.is_read,
        })
    return messages_data

# НОВИЙ ЕНДПОІНТ
@router.post("/{chat_id}/messages/read")
async def mark_messages_as_read_endpoint( # Перейменовано
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    chat_check_result = await session.execute(
        select(chat).where(chat.c.id == chat_id)
    )
    chat_row = chat_check_result.mappings().first()

    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Немає доступу до чату або чат не знайдено")

    partner_id = chat_row["user1_id"] if chat_row["user2_id"] == current_user.id else chat_row["user2_id"]

    stmt = (
        update(message)
        .where(
            (message.c.chat_id == chat_id) &
            (message.c.sender_id == partner_id) & # Тільки повідомлення від співрозмовника
            (message.c.is_read == False)
        )
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.commit()

    return {"status": "success", "message": "Повідомлення від співрозмовника позначені як прочитані"}