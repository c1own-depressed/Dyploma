import os
import shutil
import uuid
from datetime import datetime, timedelta # Додано timedelta
from typing import List, Any, Dict, Optional
from fastapi import Path as FastApiPath
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, or_, update, func, desc
from starlette.responses import FileResponse

# Переконайтеся, що User тут - це ваша Pydantic модель користувача від FastAPI Users
# а user_table - це SQLAlchemy Table об'єкт
from auth.database import get_async_session, User
from models.models import chat, task, message
from models.models import user as user_table # Імпортуємо таблицю user як user_table
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
# Директорія для збереження завантажених файлів чату
# ВАЖЛИВО: Для продакшену використовуйте змінні середовища та розгляньте хмарні сховища (S3, GCS)
UPLOAD_DIR = "./uploaded_chat_files"
os.makedirs(UPLOAD_DIR, exist_ok=True) # Створюємо директорію, якщо її немає

async def get_current_active_user_and_update_last_seen(
    current_user_dependency: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session)
):
    if current_user_dependency:
        stmt = (
            update(user_table)
            .where(user_table.c.id == current_user_dependency.id)
            .values(last_seen=datetime.utcnow())
        )
        await session.execute(stmt)
        await session.commit()
    return current_user_dependency

async def get_partner_details(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(user_table.c.username, user_table.c.last_seen).where(user_table.c.id == user_id)
    )
    partner_db_details = result.mappings().first()
    if not partner_db_details:
        return {"username": "Unknown", "last_seen": None, "is_online": False}
    is_online = False
    if partner_db_details["last_seen"]:
        last_seen_dt = partner_db_details["last_seen"]
        if isinstance(last_seen_dt, str):
            try: last_seen_dt = datetime.fromisoformat(last_seen_dt)
            except ValueError:
                 try: last_seen_dt = datetime.strptime(last_seen_dt, "%Y-%m-%d %H:%M:%S.%f")
                 except ValueError: last_seen_dt = None
        if last_seen_dt:
            if last_seen_dt.tzinfo: last_seen_dt = last_seen_dt.replace(tzinfo=None)
            current_utc_time = datetime.utcnow()
            if current_utc_time - last_seen_dt < timedelta(minutes=5): is_online = True
    return {"username": partner_db_details["username"], "is_online": is_online}

@router.post("/with-owner/{task_id}")
async def create_chat_with_owner(
    task_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    result = await session.execute(select(task).where(task.c.id == task_id))
    task_row = result.mappings().first()
    if not task_row: raise HTTPException(status_code=404, detail="Task not found")
    customer_id = task_row["customer_id"]
    executor_id = current_user.id
    if customer_id == executor_id: raise HTTPException(status_code=400, detail="Cannot create chat with yourself")
    existing_chat = await session.execute(select(chat.c.id).where(or_((chat.c.user1_id == customer_id) & (chat.c.user2_id == executor_id),(chat.c.user1_id == executor_id) & (chat.c.user2_id == customer_id))))
    chat_row = existing_chat.first()
    if chat_row: return {"chat_id": chat_row[0]}
    new_chat = await session.execute(insert(chat).values(user1_id=customer_id,user2_id=executor_id,task_id=task_id,created_at=datetime.utcnow()).returning(chat.c.id))
    await session.commit()
    chat_id = new_chat.scalar()
    return {"chat_id": chat_id}

@router.get("/", response_model=List[Dict[str, Any]])
async def get_user_chats(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    user_chats_select = await session.execute(
        select(chat.c.id, chat.c.user1_id, chat.c.user2_id)
        .where(or_(chat.c.user1_id == current_user.id, chat.c.user2_id == current_user.id))
    )
    user_chats_list = user_chats_select.mappings().fetchall()
    if not user_chats_list: return []
    chats_data = []
    for chat_item_map in user_chats_list:
        partner_id = chat_item_map["user1_id"] if chat_item_map["user2_id"] == current_user.id else chat_item_map["user2_id"]
        partner_details = await get_partner_details(partner_id, session)
        last_message_select = await session.execute(
            select(message.c.content, message.c.created_at, message.c.sender_id, message.c.is_read, message.c.original_file_name) # Додано original_file_name для сніпета
            .where(message.c.chat_id == chat_item_map["id"])
            .order_by(message.c.created_at.desc()).limit(1)
        )
        last_msg_obj = last_message_select.mappings().first()
        last_message_snippet = None
        last_message_timestamp = None
        last_message_sent_by_me = None
        is_last_message_read_by_partner = None
        if last_msg_obj:
            content = last_msg_obj["content"]
            file_name_snippet = last_msg_obj["original_file_name"]

            if content:
                last_message_snippet = content[:40] + "..." if len(content) > 40 else content
            elif file_name_snippet:
                last_message_snippet = f"Файл: {file_name_snippet[:30]}"
                if len(file_name_snippet) > 30: last_message_snippet += "..."
            else:
                last_message_snippet = "Повідомлення без тексту"

            created_at_dt = last_msg_obj["created_at"]
            if isinstance(created_at_dt, datetime):
                last_message_timestamp = created_at_dt.isoformat() + "Z"
            else:
                last_message_timestamp = str(created_at_dt)

            last_message_sent_by_me = (last_msg_obj["sender_id"] == current_user.id)
            if last_message_sent_by_me:
                is_last_message_read_by_partner = last_msg_obj["is_read"]
        unread_count_select = await session.execute(
            select(func.count(message.c.id))
            .where((message.c.chat_id == chat_item_map["id"]) & (message.c.sender_id == partner_id) & (message.c.is_read == False))
        )
        unread_messages_count = unread_count_select.scalar_one_or_none() or 0
        chats_data.append({
            "id": chat_item_map["id"], "partner_name": partner_details["username"],
            "partner_is_online": partner_details["is_online"], "last_message_snippet": last_message_snippet,
            "last_message_timestamp": last_message_timestamp, "last_message_sent_by_me": last_message_sent_by_me,
            "is_last_message_read_by_partner": is_last_message_read_by_partner,
            "unread_messages_count": unread_messages_count,
        })
    chats_data.sort(
        key=lambda x: datetime.fromisoformat(x["last_message_timestamp"].replace("Z", "+00:00")) if x["last_message_timestamp"] else datetime.min.replace(tzinfo=None),
        reverse=True
    )
    return chats_data

@router.get("/{chat_id}")
async def get_chat_by_id(
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    result = await session.execute(select(chat).where(chat.c.id == chat_id))
    chat_row = result.mappings().first()
    if not chat_row: raise HTTPException(status_code=404, detail="Chat not found")
    if current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]: raise HTTPException(status_code=403, detail="Access denied")
    partner_id = chat_row["user1_id"] if chat_row["user2_id"] == current_user.id else chat_row["user2_id"]
    partner_details = await get_partner_details(partner_id, session)
    return {"id": chat_row["id"], "partner_name": partner_details["username"], "partner_is_online": partner_details["is_online"]}


@router.post("/{chat_id}/messages")
async def send_message_endpoint(
    chat_id: int,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Повідомлення повинно містити текст або файл.")

    result = await session.execute(select(chat).where(chat.c.id == chat_id))
    chat_row = result.mappings().first()
    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Немає доступу до чату")

    file_path_in_db = None
    original_filename_for_db = None
    mime_type_for_db = None

    if file:
        original_filename_for_db = file.filename
        mime_type_for_db = file.content_type
        file_extension = os.path.splitext(original_filename_for_db)[1]
        # Генеруємо унікальне ім'я файлу для зберігання на сервері
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        server_file_path = os.path.join(UPLOAD_DIR, unique_filename)
        file_path_in_db = unique_filename # Зберігаємо в БД тільки унікальне ім'я

        try:
            with open(server_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            # Тут можна додати логування помилки
            raise HTTPException(status_code=500, detail=f"Не вдалося зберегти файл: {str(e)}")
        finally:
            await file.close() # Завжди закриваємо файл

    new_msg_stmt = insert(message).values(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=text.strip() if text else None,
        created_at=datetime.utcnow(),
        is_read=False,
        file_path=file_path_in_db,
        original_file_name=original_filename_for_db,
        mime_type=mime_type_for_db
    ).returning(
        message.c.id, message.c.content, message.c.sender_id,
        message.c.created_at, message.c.is_read,
        message.c.file_path, message.c.original_file_name, message.c.mime_type
    )
    new_msg_result = await session.execute(new_msg_stmt)
    await session.commit()
    msg_db_data = new_msg_result.mappings().first()

    if not msg_db_data:
        raise HTTPException(status_code=500, detail="Не вдалося створити повідомлення")

    created_at_iso = (msg_db_data["created_at"].isoformat() + "Z") if isinstance(msg_db_data["created_at"], datetime) else str(msg_db_data["created_at"])

    file_url = None
    if msg_db_data["file_path"]:
        # ВАЖЛИВО: Це URL для локального розгортання. Для продакшену потрібен інший підхід.
        # Наприклад, request.url_for('get_chat_attachment', filename=msg_db_data["file_path"])
        # Або URL з хмарного сховища.
        file_url = f"http://localhost:8000/chats/attachments/{msg_db_data['file_path']}"


    return {
        "id": msg_db_data["id"],
        "text": msg_db_data["content"],
        "sender": "me", # Оскільки це відповідь на відправку поточним користувачем
        "created_at": created_at_iso,
        "is_read": msg_db_data["is_read"],
        "file_url": file_url,
        "original_file_name": msg_db_data["original_file_name"],
        "mime_type": msg_db_data["mime_type"]
    }

@router.get("/{chat_id}/messages", response_model=List[Dict[str, Any]])
async def get_messages_endpoint(
    chat_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    result = await session.execute(select(chat).where(chat.c.id == chat_id))
    chat_row = result.mappings().first()
    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Немає доступу до чату")

    offset = (page - 1) * page_size
    messages_query = (
        select(
            message.c.id, message.c.content, message.c.sender_id,
            message.c.created_at, message.c.is_read,
            message.c.file_path, message.c.original_file_name, message.c.mime_type # Додано поля файлів
        )
        .where(message.c.chat_id == chat_id).order_by(message.c.created_at.asc())
        .offset(offset).limit(page_size)
    )
    db_messages_result = await session.execute(messages_query)
    db_messages_rows = db_messages_result.fetchall() # Змінено ім'я змінної
    if not db_messages_rows: return []

    messages_response_data = [] # Змінено ім'я змінної
    for msg_row_data in db_messages_rows: # Змінено ім'я змінної
        sender_type = "me" if msg_row_data.sender_id == current_user.id else "other"
        created_at_iso = (msg_row_data.created_at.isoformat() + "Z") if isinstance(msg_row_data.created_at, datetime) else str(msg_row_data.created_at)

        file_url = None
        if msg_row_data.file_path:
            file_url = f"http://localhost:8000/chats/attachments/{msg_row_data.file_path}"

        messages_response_data.append({
            "id": msg_row_data.id,
            "text": msg_row_data.content,
            "sender": sender_type,
            "created_at": created_at_iso,
            "is_read": msg_row_data.is_read,
            "file_url": file_url,
            "original_file_name": msg_row_data.original_file_name,
            "mime_type": msg_row_data.mime_type
        })
    return messages_response_data

# Ендпоінт для віддачі файлів
# ВАЖЛИВО: Цей ендпоінт потребує належної АВТЕНТИФІКАЦІЇ та АВТОРИЗАЦІЇ
# щоб файли могли завантажувати тільки авторизовані користувачі чату.
# Поточна реалізація є базовою і НЕБЕЗПЕЧНОЮ для продакшену без цих перевірок.
@router.get("/attachments/{filename:path}")
async def get_chat_attachment(
    filename: str = FastApiPath(...),
    # current_user: User = Depends(fastapi_users.current_user(active=True)) # Потрібно для перевірки доступу
    # session: AsyncSession = Depends(get_async_session) # Потрібно для перевірки доступу
):
    # Тут має бути логіка перевірки, чи має поточний користувач доступ до файлу 'filename'.
    # Наприклад, знайти повідомлення з file_path == filename, перевірити chat_id,
    # і чи є current_user учасником цього чату.

    file_on_disk_path = os.path.join(UPLOAD_DIR, filename) # Змінено ім'я змінної
    if not os.path.isfile(file_on_disk_path):
        raise HTTPException(status_code=404, detail="Файл не знайдено")

    # Можна спробувати отримати original_file_name з БД для Content-Disposition,
    # але для простоти зараз FileResponse сам визначить ім'я з шляху.
    # Або передати filename=original_filename_from_db (потребує запиту до БД)
    return FileResponse(path=file_on_disk_path, filename=filename) # filename тут - це унікальне ім'я з UUID


# ... (існуючі ендпоінти mark_messages_as_read_endpoint, ping_user_online) ...
@router.post("/{chat_id}/messages/read")
async def mark_messages_as_read_endpoint(
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    chat_check_result = await session.execute(select(chat).where(chat.c.id == chat_id))
    chat_row = chat_check_result.mappings().first()
    if not chat_row or current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]: raise HTTPException(status_code=403, detail="Немає доступу до чату або чат не знайдено")
    partner_id = chat_row["user1_id"] if chat_row["user2_id"] == current_user.id else chat_row["user2_id"]
    stmt = (update(message).where((message.c.chat_id == chat_id) & (message.c.sender_id == partner_id) & (message.c.is_read == False)).values(is_read=True))
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", "message": "Повідомлення від співрозмовника позначені як прочитані"}

@router.post("/me/ping-online", tags=["User Actions"])
async def ping_user_online(
    current_user: User = Depends(get_current_active_user_and_update_last_seen)
):
    return {"status": "success", "message": f"User {current_user.id} pinged online."}
