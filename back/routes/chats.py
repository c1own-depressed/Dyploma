import os
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Any, Dict, Optional
from fastapi import Path as FastApiPath
from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, or_, update, func, desc, delete # <--- ДОДАНО delete
from starlette.responses import FileResponse

from auth.database import get_async_session, User
from models.models import chat, task, message
from models.models import user as user_table
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

UPLOAD_DIR = "./uploaded_chat_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    new_chat_stmt = insert(chat).values(user1_id=customer_id,user2_id=executor_id,task_id=task_id,created_at=datetime.utcnow()).returning(chat.c.id)
    new_chat_result = await session.execute(new_chat_stmt) # Змінено тут для отримання результату
    await session.commit()
    chat_id = new_chat_result.scalar_one() # Використовуємо scalar_one() для отримання ID
    return {"chat_id": chat_id}


@router.get("/", response_model=List[Dict[str, Any]])
async def get_user_chats(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    # Запитуємо також поля userX_last_typing_at
    user_chats_query = select(
        chat.c.id,
        chat.c.user1_id,
        chat.c.user2_id,
        chat.c.user1_last_typing_at,  # Додано
        chat.c.user2_last_typing_at  # Додано
    ).where(or_(chat.c.user1_id == current_user.id, chat.c.user2_id == current_user.id))

    user_chats_select_result = await session.execute(user_chats_query)
    user_chats_list = user_chats_select_result.mappings().fetchall()

    if not user_chats_list:
        return []

    chats_data = []
    # Поріг часу, протягом якого вважається, що співрозмовник все ще друкує (наприклад, 5 секунд)
    typing_threshold_time = datetime.utcnow() - timedelta(seconds=5)

    for chat_item_map in user_chats_list:
        partner_id = chat_item_map["user1_id"] if chat_item_map["user2_id"] == current_user.id else chat_item_map[
            "user2_id"]
        partner_details = await get_partner_details(partner_id, session)

        # Визначаємо, чи друкує партнер
        partner_is_typing = False
        if chat_item_map["user1_id"] == partner_id:  # Якщо партнер user1
            if chat_item_map["user1_last_typing_at"] and \
                    isinstance(chat_item_map["user1_last_typing_at"], datetime) and \
                    chat_item_map["user1_last_typing_at"] > typing_threshold_time:
                partner_is_typing = True
        elif chat_item_map["user2_id"] == partner_id:  # Якщо партнер user2
            if chat_item_map["user2_last_typing_at"] and \
                    isinstance(chat_item_map["user2_last_typing_at"], datetime) and \
                    chat_item_map["user2_last_typing_at"] > typing_threshold_time:
                partner_is_typing = True

        # Отримання останнього повідомлення (існуюча логіка)
        last_message_select = await session.execute(
            select(message.c.content, message.c.created_at, message.c.sender_id, message.c.is_read,
                   message.c.original_file_name)
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
            else:  # Fallback if it's somehow not a datetime object already
                try:
                    last_message_timestamp = datetime.fromisoformat(
                        str(created_at_dt).replace("Z", "+00:00")).isoformat() + "Z"
                except:
                    last_message_timestamp = str(created_at_dt)

            last_message_sent_by_me = (last_msg_obj["sender_id"] == current_user.id)
            if last_message_sent_by_me:
                is_last_message_read_by_partner = last_msg_obj["is_read"]

        unread_count_select = await session.execute(
            select(func.count(message.c.id))
            .where((message.c.chat_id == chat_item_map["id"]) & (message.c.sender_id == partner_id) & (
                        message.c.is_read == False))
        )
        unread_messages_count = unread_count_select.scalar_one_or_none() or 0

        chats_data.append({
            "id": chat_item_map["id"],
            "partner_name": partner_details["username"],
            "partner_is_online": partner_details["is_online"],
            "partner_is_typing": partner_is_typing,  # <--- НОВЕ ПОЛЕ
            "last_message_snippet": last_message_snippet,
            "last_message_timestamp": last_message_timestamp,
            "last_message_sent_by_me": last_message_sent_by_me,
            "is_last_message_read_by_partner": is_last_message_read_by_partner,
            "unread_messages_count": unread_messages_count,
        })

    # Сортування (існуюча логіка)
    chats_data.sort(
        key=lambda x: datetime.fromisoformat(x["last_message_timestamp"].replace("Z", "+00:00")) if x[
            "last_message_timestamp"] else datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )
    return chats_data

@router.get("/{chat_id}") # Цей ендпоінт вже є
async def get_chat_by_id(
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    result = await session.execute(
        select(
            chat.c.id,
            chat.c.user1_id,
            chat.c.user2_id,
            chat.c.user1_last_typing_at, # Додано
            chat.c.user2_last_typing_at  # Додано
        ).where(chat.c.id == chat_id)
    )
    chat_row = result.mappings().first()
    if not chat_row: raise HTTPException(status_code=404, detail="Chat not found")
    if current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Access denied")

    partner_id = chat_row["user1_id"] if chat_row["user2_id"] == current_user.id else chat_row["user2_id"]
    partner_details = await get_partner_details(partner_id, session) # Це вже є

    partner_is_typing = False
    # Поріг часу, протягом якого вважається, що співрозмовник все ще друкує (наприклад, 5 секунд)
    typing_threshold_time = datetime.utcnow() - timedelta(seconds=5)

    if chat_row["user1_id"] == partner_id:
        if chat_row["user1_last_typing_at"] and chat_row["user1_last_typing_at"] > typing_threshold_time:
            partner_is_typing = True
    elif chat_row["user2_id"] == partner_id:
        if chat_row["user2_last_typing_at"] and chat_row["user2_last_typing_at"] > typing_threshold_time:
            partner_is_typing = True

    return {
        "id": chat_row["id"],
        "partner_name": partner_details["username"],
        "partner_is_online": partner_details["is_online"],
        "partner_is_typing": partner_is_typing # Нове поле
    }

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
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        server_file_path = os.path.join(UPLOAD_DIR, unique_filename)
        file_path_in_db = unique_filename

        try:
            with open(server_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Не вдалося зберегти файл: {str(e)}")
        finally:
            await file.close()

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
        file_url = f"http://localhost:8000/chats/attachments/{msg_db_data['file_path']}"


    return {
        "id": msg_db_data["id"],
        "text": msg_db_data["content"],
        "sender": "me",
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
            message.c.file_path, message.c.original_file_name, message.c.mime_type
        )
        .where(message.c.chat_id == chat_id).order_by(message.c.created_at.asc()) # Змінено на .asc() для правильного порядку
        .offset(offset).limit(page_size)
    )
    db_messages_result = await session.execute(messages_query)
    db_messages_rows = db_messages_result.fetchall()
    if not db_messages_rows: return []

    messages_response_data = []
    for msg_row_data in db_messages_rows:
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

@router.get("/attachments/{filename:path}")
async def get_chat_attachment(
    filename: str = FastApiPath(...),
):
    file_on_disk_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_on_disk_path):
        raise HTTPException(status_code=404, detail="Файл не знайдено")
    return FileResponse(path=file_on_disk_path, filename=filename)


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

# НОВИЙ ЕНДПОІНТ ДЛЯ ВИДАЛЕННЯ ЧАТУ
@router.delete("/{chat_id}", status_code=200)
async def delete_chat_endpoint(
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    # 1. Отримати чат для перевірки існування та участі користувача
    chat_select_stmt = select(chat).where(chat.c.id == chat_id)
    chat_result = await session.execute(chat_select_stmt)
    chat_to_delete = chat_result.mappings().first()

    if not chat_to_delete:
        raise HTTPException(status_code=404, detail="Chat not found")

    # 2. Перевірити, чи є поточний користувач учасником цього чату
    if current_user.id not in [chat_to_delete["user1_id"], chat_to_delete["user2_id"]]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chat")

    # 3. Видалити повідомлення, пов'язані з чатом
    #    Це важливо, якщо ON DELETE CASCADE не встановлено для зовнішнього ключа в таблиці повідомлень.
    #    Якщо встановлено, цей крок можна пропустити, оскільки БД зробить це автоматично.
    delete_messages_stmt = delete(message).where(message.c.chat_id == chat_id)
    await session.execute(delete_messages_stmt)

    # 4. Видалити сам чат
    delete_chat_stmt = delete(chat).where(chat.c.id == chat_id)
    await session.execute(delete_chat_stmt)

    # 5. Застосувати транзакцію
    await session.commit()

    return {"status": "success", "message": "Chat deleted successfully"}

@router.post("/{chat_id}/typing", status_code=200)
async def user_is_typing(
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user_and_update_last_seen),
):
    chat_select_stmt = select(chat).where(chat.c.id == chat_id)
    chat_result = await session.execute(chat_select_stmt)
    chat_row = chat_result.mappings().first()

    if not chat_row:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in [chat_row["user1_id"], chat_row["user2_id"]]:
        raise HTTPException(status_code=403, detail="Not authorized for this chat")

    now_utc = datetime.utcnow()
    update_values = {}
    if chat_row["user1_id"] == current_user.id:
        update_values = {"user1_last_typing_at": now_utc}
    elif chat_row["user2_id"] == current_user.id:
        update_values = {"user2_last_typing_at": now_utc}

    if update_values:
        stmt = update(chat).where(chat.c.id == chat_id).values(**update_values)
        await session.execute(stmt)
        await session.commit()
        return {"status": "success", "message": "Typing status updated"}

    raise HTTPException(status_code=400, detail="Could not update typing status")
