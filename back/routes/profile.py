from typing import List

from fastapi import APIRouter, Depends,HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import join, update, func
from auth.auth import auth_backend
from auth.database import get_async_session, User
from auth.manager import get_user_manager
from models.models import startup, task, user as user_table, rating  # ← Імпортуємо таблиці core
from fastapi_users import FastAPIUsers
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    registered_at: datetime
    role_id: int
    is_active: bool
    is_superuser: bool
    is_verified: bool

    class Config:
        orm_mode = True

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    status: str
    owner_name: str

    class Config:
        orm_mode = True

@router.get("/profile", response_model=UserResponse)
async def get_profile(user: User = Depends(fastapi_users.current_user())):
    return user

@router.get("/tasks", response_model=list[TaskResponse])
async def get_user_tasks(
    user: User = Depends(fastapi_users.current_user()),  # this is user object
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(
            task.c.id,
            task.c.title,
            task.c.description,
            task.c.created_at,
            task.c.status,
            user_table.c.username.label("owner_name"),  # <- use renamed user_table
        )
        .select_from(
            join(task, user_table, task.c.customer_id == user_table.c.id)
        )
        .where(
            task.c.executor_id == user.id,
            task.c.status != 'paid'
        )
    )

    result = await session.execute(stmt)
    rows = result.fetchall()

    return [
        TaskResponse(
            id=row.id,
            title=row.title,
            description=row.description,
            created_at=row.created_at,
            status=row.status,
            owner_name=row.owner_name,
        )
        for row in rows
    ]

# Схема для задач
class TaskInStartupResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str

    class Config:
        orm_mode = True

# Схема для стартапів
class StartupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    tasks: List[TaskInStartupResponse]

    class Config:
        orm_mode = True

@router.get("/startups", response_model=List[StartupResponse])
async def get_user_startups(
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    # Отримуємо всі стартапи користувача
    result = await session.execute(
        select(
            startup.c.id,
            startup.c.name,
            startup.c.description
        ).where(startup.c.owner_id == user.id)
    )
    startup_rows = result.fetchall()

    # Мапа для задач по стартапах
    task_map = {}
    task_result = await session.execute(select(task))
    task_rows = task_result.fetchall()

    for row in task_rows:
        task_data = row._mapping
        task_map.setdefault(task_data["startup_id"], []).append(TaskInStartupResponse(
            id=task_data["id"],
            title=task_data["title"],
            description=task_data["description"],
            status=task_data["status"]
        ))

    # Формуємо список стартапів з їхніми задачами
    startups_with_tasks = []
    for s in startup_rows:
        startup_data = s._mapping
        startups_with_tasks.append(
            StartupResponse(
                id=startup_data["id"],
                name=startup_data["name"],
                description=startup_data["description"],
                tasks=task_map.get(startup_data["id"], [])
            )
        )

    return startups_with_tasks

class TaskStatusUpdate(BaseModel):
    status: str

@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: int = Path(..., gt=0),
    payload: TaskStatusUpdate = ...,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    # Перевірити, чи задача існує і чи є виконавець поточним користувачем
    result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    existing_task = result.fetchone()

    if not existing_task:
        raise HTTPException(status_code=404, detail="Задачу не знайдено")

    task_data = existing_task._mapping

    if task_data["executor_id"] != user.id:
        raise HTTPException(status_code=403, detail="Немає прав на зміну цієї задачі")

    # Оновити статус
    await session.execute(
        update(task)
        .where(task.c.id == task_id)
        .values(status=payload.status)
    )
    await session.commit()

    return {"message": f"Статус задачі оновлено на '{payload.status}'"}

# Схема для рейтингу користувача
class UserRatingResponse(BaseModel):
    user_id: int
    average_rating: float

    class Config:
        orm_mode = True

@router.get("/rating", response_model=UserRatingResponse)
async def get_user_rating(
    user=Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        select(func.avg(rating.c.rating).label("avg_rating"))
        .where(rating.c.executor_id == user.id)
    )

    result = await session.execute(stmt)
    avg_rating = result.scalar()

    if avg_rating is None:
        avg_rating = 0.0

    return UserRatingResponse(
        user_id=user.id,
        average_rating=round(avg_rating, 2)
    )