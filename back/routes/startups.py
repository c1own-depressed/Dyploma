# routes/startups.py

from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from auth.database import get_async_session, User
from auth.manager import get_user_manager
from models.models import startup, task, user

router = APIRouter(
    prefix="/startups",
    tags=["startups"]
)

# Схеми відповіді
class TaskSchema(BaseModel):
    id: int  # Додаємо id
    title: str

    class Config:
        orm_mode = True

class UserSchema(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class StartupSchema(BaseModel):
    id: int
    name: str
    description: str | None
    owner_username: str  # додано
    tasks: List[TaskSchema]

    class Config:
        orm_mode = True

@router.get("/", response_model=List[StartupSchema])
async def get_startups(session: AsyncSession = Depends(get_async_session)):
    # JOIN startups з user по owner_id
    stmt = (
        select(
            startup.c.id,
            startup.c.name,
            startup.c.description,
            user.c.username.label("owner_username"),
        )
        .select_from(startup.join(user, startup.c.owner_id == user.c.id))
    )
    result = await session.execute(stmt)
    startups_raw = result.fetchall()

    # Отримуємо всі задачі
    result_tasks = await session.execute(select(task))
    tasks_raw = result_tasks.fetchall()

    # Мапа: startup_id -> список задач
    task_map = {}
    for row in tasks_raw:
        t = row._mapping
        task_map.setdefault(t["startup_id"], []).append({"id": t["id"], "title": t["title"]})

    # Формування відповіді
    startups_with_tasks = []
    for row in startups_raw:
        s = row._mapping
        startups_with_tasks.append({
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "owner_username": s["owner_username"],  # додано
            "tasks": task_map.get(s["id"], [])
        })

    return startups_with_tasks

from fastapi import HTTPException, status
from sqlalchemy import insert
from models.models import comment as comment_table  # уникаємо конфлікту з Python comment
from auth.auth import auth_backend  # функція для отримання поточного користувача
from datetime import datetime
class CommentSchema(BaseModel):
    id: int
    text: str
    created_at: datetime
    author: str

    class Config:
        orm_mode = True


class CommentCreateSchema(BaseModel):
    text: str

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

@router.get("/{startup_id}/comments", response_model=List[CommentSchema])
async def get_comments(startup_id: int, session: AsyncSession = Depends(get_async_session)):
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
    return result.mappings().all()


@router.post("/{startup_id}/comments", response_model=CommentSchema)
async def add_comment(
    startup_id: int,
    comment_data: CommentCreateSchema,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(fastapi_users.current_user()),
):
    if not comment_data.text.strip():
        raise HTTPException(status_code=400, detail="Текст коментаря не може бути порожнім")

    stmt = insert(comment_table).values(
        text=comment_data.text,
        created_at=datetime.utcnow(),
        user_id=current_user.id,
        startup_id=startup_id,
    ).returning(
        comment_table.c.id,
        comment_table.c.text,
        comment_table.c.created_at,
    )

    result = await session.execute(stmt)
    await session.commit()
    new_comment = result.fetchone()

    return {
        "id": new_comment.id,
        "text": new_comment.text,
        "created_at": new_comment.created_at,
        "author": current_user.username,
    }
