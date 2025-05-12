from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import join, update, func
from auth.auth import auth_backend
from auth.database import get_async_session, User  # Переконайтесь, що User імпортовано правильно
from auth.manager import get_user_manager
from models.models import startup, task, user as user_table, rating
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
    owner_name: str  # Додано з попереднього кроку

    class Config:
        orm_mode = True


@router.get("/profile", response_model=UserResponse)
async def get_profile(user: User = Depends(fastapi_users.current_user())):
    return user


@router.get("/tasks", response_model=list[TaskResponse])
async def get_user_tasks(
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(
            task.c.id,
            task.c.title,
            task.c.description,
            task.c.created_at,
            task.c.status,
            user_table.c.username.label("owner_name")
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


# Оновлений ендпоінт для відмови від завдання
@router.put("/tasks/{task_id}/refuse")
async def refuse_task_endpoint(
        task_id: int = Path(..., description="ID завдання, від якого відмовляються", gt=0),
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    # Прибираємо 'async with session.begin():', оскільки транзакція вже розпочата

    result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    current_task = result.fetchone()

    if not current_task:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    current_task_data = current_task._mapping

    if current_task_data["executor_id"] != user.id:
        raise HTTPException(status_code=403,
                            detail="Ви не є виконавцем цього завдання і не можете від нього відмовитись")

    if current_task_data["status"] != 'in_progress':
        raise HTTPException(
            status_code=400,
            detail=f"Неможливо відмовитися від завдання зі статусом '{current_task_data['status']}'. Відмова можлива тільки для завдань у статусі 'in_progress'."
        )

    stmt = (
        update(task)
        .where(task.c.id == task_id)
        .values(status='pending', executor_id=None)
    )
    await session.execute(stmt)

    # Явний коміт, аналогічно до update_task_status
    await session.commit()

    return {"message": "Ви успішно відмовилися від завдання. Воно було повернено в пул доступних завдань."}


class TaskInStartupResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str

    # Можливо, варто додати executor_id, щоб бачити, чи призначений хтось
    # executor_id: int | None = None

    class Config:
        orm_mode = True


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
    result = await session.execute(
        select(
            startup.c.id,
            startup.c.name,
            startup.c.description
        ).where(startup.c.owner_id == user.id)
    )
    startup_rows = result.fetchall()

    if not startup_rows:
        return []

    startup_ids = [s.id for s in startup_rows]

    task_map = {}
    task_result_stmt = select(task).where(task.c.startup_id.in_(startup_ids))
    task_rows_result = await session.execute(task_result_stmt)
    all_tasks_for_startups = task_rows_result.fetchall()

    for task_row_data in all_tasks_for_startups:
        task_data = task_row_data._asdict()  # Використовуємо _asdict() для легкого доступу
        task_response = TaskInStartupResponse(
            id=task_data["id"],
            title=task_data["title"],
            description=task_data["description"],
            status=task_data["status"],
            # executor_id=task_data.get("executor_id") # Якщо додали поле
        )
        task_map.setdefault(task_data["startup_id"], []).append(task_response)

    startups_with_tasks = []
    for s_row in startup_rows:
        startup_data = s_row._asdict()
        startups_with_tasks.append(
            StartupResponse(
                id=startup_data["id"],
                name=startup_data["name"],
                description=startup_data["description"],
                tasks=task_map.get(startup_data["id"], [])
            )
        )
    return startups_with_tasks


# --- Новий ендпоінт для власника стартапу для відключення виконавця ---
@router.put("/startups/tasks/{task_id}/remove-executor", tags=["startups", "tasks"])
async def owner_remove_task_executor(
        task_id: int = Path(..., description="ID завдання, з якого потрібно зняти виконавця", gt=0),
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    # 1. Отримати завдання
    task_result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    current_task_row = task_result.fetchone()

    if not current_task_row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    current_task_data = current_task_row._asdict()

    # 2. Перевірити статус завдання ('in_progress')
    if current_task_data["status"] != 'in_progress':
        raise HTTPException(
            status_code=400,
            detail=f"Неможливо зняти виконавця із завдання зі статусом '{current_task_data['status']}'. Дозволено тільки для статусу 'in_progress'."
        )

    # 3. Перевірити, чи є взагалі виконавець у завдання
    if current_task_data["executor_id"] is None:
        raise HTTPException(
            status_code=400,
            detail="У цього завдання немає призначеного виконавця, щоб його відключати."
        )

    # 4. Отримати стартап, до якого належить завдання
    startup_id = current_task_data["startup_id"]
    if not startup_id:
        # Цей випадок малоймовірний, якщо дані консистентні
        raise HTTPException(status_code=500, detail="Внутрішня помилка: завдання не прив'язане до стартапу.")

    startup_result = await session.execute(
        select(startup).where(startup.c.id == startup_id)
    )
    parent_startup_row = startup_result.fetchone()

    if not parent_startup_row:
        raise HTTPException(status_code=404, detail="Стартап, до якого належить завдання, не знайдено.")

    parent_startup_data = parent_startup_row._asdict()

    # 5. Перевірити, чи поточний користувач є власником стартапу
    if parent_startup_data["owner_id"] != user.id:
        raise HTTPException(status_code=403,
                            detail="Ви не є власником цього стартапу і не можете керувати виконавцями його завдань.")

    # 6. Оновити статус завдання на 'pending' та скинути executor_id
    update_stmt = (
        update(task)
        .where(task.c.id == task_id)
        .values(status='pending', executor_id=None)
    )
    await session.execute(update_stmt)
    await session.commit()

    return {"message": "Виконавця успішно відключено від завдання. Статус завдання оновлено на 'pending'."}


class TaskStatusUpdate(BaseModel):
    status: str


@router.put("/tasks/{task_id}/status")
async def update_task_status(
        task_id: int = Path(..., gt=0),
        payload: TaskStatusUpdate = ...,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    existing_task_row = result.fetchone()

    if not existing_task_row:
        raise HTTPException(status_code=404, detail="Задачу не знайдено")

    existing_task_data = existing_task_row._mapping

    # Додано перевірку: чи є користувач замовником або виконавцем завдання
    # Або чи є він власником стартапу, до якого належить завдання
    # (залежно від вашої бізнес-логіки, хто може змінювати статус)
    # Поточна логіка дозволяє змінювати статус тільки виконавцю
    if existing_task_data["executor_id"] != user.id:
        # Додатково можна перевірити, чи є користувач власником стартапу (якщо така логіка потрібна)
        # startup_of_task_result = await session.execute(select(startup).where(startup.c.id == existing_task_data.startup_id))
        # startup_of_task = startup_of_task_result.fetchone()
        # if not startup_of_task or startup_of_task._mapping["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail="Немає прав на зміну статусу цієї задачі")

    await session.execute(
        update(task)
        .where(task.c.id == task_id)
        .values(status=payload.status)
    )
    await session.commit()

    return {"message": f"Статус задачі оновлено на '{payload.status}'"}


class UserRatingResponse(BaseModel):
    user_id: int
    average_rating: float  # Може бути None, якщо рейтингів немає

    class Config:
        orm_mode = True


@router.get("/rating", response_model=UserRatingResponse)
async def get_user_rating(
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        select(func.avg(rating.c.rating).label("avg_rating"))
        .where(rating.c.executor_id == user.id)
    )
    result = await session.execute(stmt)
    avg_rating_value = result.scalar()  # scalar_one_or_none, якщо очікується None

    # Забезпечуємо, що average_rating є float, навіть якщо avg_rating_value is None
    final_avg_rating = 0.0
    if avg_rating_value is not None:
        final_avg_rating = round(float(avg_rating_value), 2)

    return UserRatingResponse(
        user_id=user.id,
        average_rating=final_avg_rating
    )