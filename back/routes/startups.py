# routes/startups.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert # select вже імпортовано, insert теж
from typing import List
from pydantic import BaseModel

from auth.database import get_async_session, User # User потрібен для FastAPIUsers
from auth.manager import get_user_manager
from models.models import startup, task, user, comment as comment_table # Імпортуємо startup як Table
from auth.auth import auth_backend
from datetime import datetime, timezone

router = APIRouter(
    prefix="/startups",
    tags=["startups"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

def ensure_aware_utc(dt: datetime | None) -> datetime | None:
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class TaskSchema(BaseModel):
    id: int
    title: str
    status: str  # <--- ДОДАНО поле статусу

    class Config:
        orm_mode = True

class UserSchema(BaseModel): # Залишаємо, якщо використовується десь ще
    id: int
    username: str

    class Config:
        orm_mode = True

class StartupSchema(BaseModel):
    id: int
    name: str
    description: str | None
    owner_username: str
    tasks: List[TaskSchema] # Тепер TaskSchema містить статус

    class Config:
        orm_mode = True

class CommentCreateSchema(BaseModel):
    text: str

class CommentSchema(BaseModel):
    id: int
    text: str
    created_at: datetime
    author: str
    class Config: orm_mode = True


@router.get("/", response_model=List[StartupSchema])
async def get_startups(session: AsyncSession = Depends(get_async_session)):
    # JOIN startups з user по owner_id
    stmt_startups = ( # Перейменовано змінну для уникнення конфлікту, якщо startup - це імпорт
        select(
            startup.c.id,
            startup.c.name,
            startup.c.description,
            user.c.username.label("owner_username"),
        )
        .select_from(startup.join(user, startup.c.owner_id == user.c.id))
    )
    result_startups = await session.execute(stmt_startups)
    startups_raw = result_startups.fetchall()

    # Отримуємо всі задачі з їх статусами
    result_tasks = await session.execute(
        select(task.c.id, task.c.title, task.c.startup_id, task.c.status) # Додано task.c.status
    )
    tasks_raw = result_tasks.fetchall()

    # Мапа: startup_id -> список задач
    task_map = {}
    for t_row in tasks_raw: # Змінено назву змінної для ітерації
        t_data = t_row._mapping # Використовуємо _mapping для доступу до даних рядка
        task_map.setdefault(t_data["startup_id"], []).append(
            TaskSchema(id=t_data["id"], title=t_data["title"], status=t_data["status"]) # Передаємо статус
        )

    # Формування відповіді
    startups_with_tasks = []
    for s_row in startups_raw: # Змінено назву змінної для ітерації
        s_data = s_row._mapping
        startups_with_tasks.append(
            StartupSchema(
                id=s_data["id"],
                name=s_data["name"],
                description=s_data["description"],
                owner_username=s_data["owner_username"],
                tasks=task_map.get(s_data["id"], [])
            )
        )
    return startups_with_tasks



@router.get("/{startup_id}/comments", response_model=List[CommentSchema])
async def get_comments_for_startup(
    startup_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        select(
            comment_table.c.id,
            comment_table.c.text,
            comment_table.c.created_at,
            user.c.username.label("author")
        )
        .select_from(comment_table.join(user, comment_table.c.user_id == user.c.id))
        .where(comment_table.c.startup_id == startup_id)
        .order_by(comment_table.c.created_at.desc())
    )
    result = await session.execute(stmt)
    comments_raw = result.mappings().all()

    processed_comments = []
    for comment_data in comments_raw:
        processed_comments.append(
            CommentSchema(
                id=comment_data["id"],
                text=comment_data["text"],
                created_at=ensure_aware_utc(comment_data["created_at"]),
                author=comment_data["author"],
            )
        )
    return processed_comments


@router.post("/{startup_id}/comments", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
async def add_comment_to_startup(
    startup_id: int,
    comment_data: CommentCreateSchema,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(fastapi_users.current_user()),
):
    if not comment_data.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Текст коментаря не може бути порожнім")

    # Виправлена перевірка існування стартапу
    startup_check_stmt = select(startup.c.id).where(startup.c.id == startup_id)
    startup_exists_result = await session.execute(startup_check_stmt)
    if not startup_exists_result.fetchone(): # Перевіряємо, чи запит повернув результат
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Стартап не знайдено")

    naive_utc_now = datetime.utcnow()

    stmt = (
        insert(comment_table)
        .values(
            text=comment_data.text,
            created_at=naive_utc_now,
            user_id=current_user.id,
            startup_id=startup_id,
        )
        .returning(
            comment_table.c.id,
            comment_table.c.text,
            comment_table.c.created_at,
        )
    )

    result = await session.execute(stmt)
    await session.commit()
    new_comment_row = result.fetchone()

    if not new_comment_row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не вдалося створити коментар")

    aware_created_at = ensure_aware_utc(new_comment_row.created_at)

    return CommentSchema(
        id=new_comment_row.id,
        text=new_comment_row.text,
        created_at=aware_created_at,
        author=current_user.username,
    )