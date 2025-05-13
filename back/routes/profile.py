from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import join, update, func, desc, asc
from auth.auth import auth_backend
from auth.database import get_async_session, User
from auth.manager import get_user_manager
from models.models import startup, task, user as user_table, rating, comment
from fastapi_users import FastAPIUsers
from pydantic import BaseModel
from datetime import datetime, timezone  # Додано timezone

router = APIRouter(
    prefix="/user",
    tags=["user", "startups"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


# --- Pydantic моделі (без змін) ---
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    registered_at: datetime  # Очікує datetime
    role_id: int
    is_active: bool
    is_superuser: bool
    is_verified: bool

    class Config: orm_mode = True


class TaskResponse(BaseModel):  # Для /user/tasks
    id: int
    title: str
    description: str
    created_at: datetime  # Очікує datetime
    status: str
    owner_name: str

    class Config: orm_mode = True


class TaskInStartupResponse(BaseModel):  # Для відповіді всередині StartupResponse
    id: int
    title: str
    description: str
    status: str

    class Config: orm_mode = True


class CommentWithAuthorResponse(BaseModel):
    id: int
    text: str
    created_at: datetime  # Очікує datetime
    user_id: int
    author_username: str

    class Config: orm_mode = True


class StartupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    tasks: List[TaskInStartupResponse] = []
    comments: List[CommentWithAuthorResponse] = []

    class Config: orm_mode = True


class TaskStatusUpdate(BaseModel):
    status: str


class UserRatingResponse(BaseModel):
    user_id: int
    average_rating: float

    class Config: orm_mode = True


# --- Функція-хелпер для перетворення naive datetime в aware UTC datetime ---
def ensure_aware_utc(dt: datetime | None) -> datetime | None:
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# --- Ендпоінти ---

@router.get("/profile", response_model=UserResponse)
async def get_profile(user: User = Depends(fastapi_users.current_user())):
    # Створюємо екземпляр UserResponse з aware datetime
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        registered_at=ensure_aware_utc(user.registered_at),  # Перетворення
        role_id=user.role_id,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified
    )


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
            task.c.created_at,  # Отримуємо з БД
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

    task_responses = []
    for row in rows:
        task_responses.append(TaskResponse(
            id=row.id,
            title=row.title,
            description=row.description,
            created_at=ensure_aware_utc(row.created_at),  # Перетворення
            status=row.status,
            owner_name=row.owner_name,
        ))
    return task_responses


@router.put("/tasks/{task_id}/refuse")
async def refuse_task_endpoint(
        # ... (код без змін) ...
        task_id: int = Path(..., description="ID завдання, від якого відмовляються", gt=0),
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
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
    await session.commit()

    return {"message": "Ви успішно відмовилися від завдання. Воно було повернено в пул доступних завдань."}


@router.get("/startups", response_model=List[StartupResponse])
async def get_user_startups_with_comments_and_tasks(
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    startup_select_stmt = select(startup).where(startup.c.owner_id == user.id)
    startup_rows_result = await session.execute(startup_select_stmt)
    startup_rows = startup_rows_result.fetchall()

    if not startup_rows:
        return []

    response_startups = []
    for s_row in startup_rows:
        startup_data = s_row._asdict()
        current_startup_id = startup_data["id"]

        tasks_stmt = select(task.c.id, task.c.title, task.c.description, task.c.status).where(
            task.c.startup_id == current_startup_id)
        tasks_result = await session.execute(tasks_stmt)
        tasks_for_startup = [
            TaskInStartupResponse(id=t.id, title=t.title, description=t.description, status=t.status)
            for t in tasks_result.fetchall()
        ]

        comments_stmt = (
            select(
                comment.c.id,
                comment.c.text,
                comment.c.created_at,  # Отримуємо з БД
                comment.c.user_id,
                user_table.c.username.label("author_username")
            )
            .select_from(comment.join(user_table, comment.c.user_id == user_table.c.id))
            .where(comment.c.startup_id == current_startup_id)
            .order_by(asc(comment.c.created_at))
        )
        comments_result = await session.execute(comments_stmt)

        comments_for_startup = []
        for c_row in comments_result.fetchall():
            comments_for_startup.append(
                CommentWithAuthorResponse(
                    id=c_row.id,
                    text=c_row.text,
                    created_at=ensure_aware_utc(c_row.created_at),  # Перетворення
                    user_id=c_row.user_id,
                    author_username=c_row.author_username
                )
            )

        response_startups.append(
            StartupResponse(
                id=startup_data["id"],
                name=startup_data["name"],
                description=startup_data["description"],
                tasks=tasks_for_startup,
                comments=comments_for_startup
            )
        )
    return response_startups


@router.put("/startups/tasks/{task_id}/remove-executor", tags=["startups", "tasks"])
async def owner_remove_task_executor(
        # ... (код без змін) ...
        task_id: int = Path(..., description="ID завдання, з якого потрібно зняти виконавця", gt=0),
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    task_result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    current_task_row = task_result.fetchone()

    if not current_task_row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    current_task_data = current_task_row._asdict()

    if current_task_data["status"] != 'in_progress':
        raise HTTPException(
            status_code=400,
            detail=f"Неможливо зняти виконавця із завдання зі статусом '{current_task_data['status']}'. Дозволено тільки для статусу 'in_progress'."
        )

    if current_task_data["executor_id"] is None:
        raise HTTPException(
            status_code=400,
            detail="У цього завдання немає призначеного виконавця, щоб його відключати."
        )

    startup_id = current_task_data["startup_id"]
    if not startup_id:
        raise HTTPException(status_code=500, detail="Внутрішня помилка: завдання не прив'язане до стартапу.")

    startup_result = await session.execute(
        select(startup).where(startup.c.id == startup_id)
    )
    parent_startup_row = startup_result.fetchone()

    if not parent_startup_row:
        raise HTTPException(status_code=404, detail="Стартап, до якого належить завдання, не знайдено.")

    parent_startup_data = parent_startup_row._asdict()

    if parent_startup_data["owner_id"] != user.id:
        raise HTTPException(status_code=403,
                            detail="Ви не є власником цього стартапу і не можете керувати виконавцями його завдань.")

    update_stmt = (
        update(task)
        .where(task.c.id == task_id)
        .values(status='pending', executor_id=None)
    )
    await session.execute(update_stmt)
    await session.commit()

    return {"message": "Виконавця успішно відключено від завдання. Статус завдання оновлено на 'pending'."}


@router.put("/tasks/{task_id}/status")
async def update_task_status(
        task_id: int = Path(..., gt=0),
        payload: TaskStatusUpdate = ...,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    # ... (код без змін) ...
    result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    existing_task_row = result.fetchone()

    if not existing_task_row:
        raise HTTPException(status_code=404, detail="Задачу не знайдено")

    existing_task_data = existing_task_row._mapping

    if existing_task_data["executor_id"] != user.id:  # Перевірка, чи є користувач виконавцем
        raise HTTPException(status_code=403, detail="Немає прав на зміну статусу цієї задачі")

    await session.execute(
        update(task)
        .where(task.c.id == task_id)
        .values(status=payload.status)
    )
    await session.commit()

    return {"message": f"Статус задачі оновлено на '{payload.status}'"}


@router.get("/rating", response_model=UserRatingResponse)
async def get_user_rating(
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    # ... (код без змін) ...
    stmt = (
        select(func.avg(rating.c.rating).label("avg_rating"))
        .where(rating.c.executor_id == user.id)
    )
    result = await session.execute(stmt)
    avg_rating_value = result.scalar()

    final_avg_rating = 0.0
    if avg_rating_value is not None:
        final_avg_rating = round(float(avg_rating_value), 2)

    return UserRatingResponse(
        user_id=user.id,
        average_rating=final_avg_rating
    )


@router.delete("/startups/{startup_id}/comments/{comment_id}", status_code=204)
async def delete_startup_comment_by_owner(
        # ... (код без змін) ...
        startup_id: int = Path(..., description="ID стартапу, до якого належить коментар", gt=0),
        comment_id: int = Path(..., description="ID коментаря для видалення", gt=0),
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    startup_check_stmt = select(startup.c.id).where(
        startup.c.id == startup_id,
        startup.c.owner_id == user.id
    )
    startup_record_result = await session.execute(startup_check_stmt)
    startup_record = startup_record_result.fetchone()

    if not startup_record:
        raise HTTPException(status_code=403, detail="Стартап не знайдено або ви не є його власником.")

    comment_to_delete_stmt = select(comment.c.id).where(
        comment.c.id == comment_id,
        comment.c.startup_id == startup_id
    )
    comment_record_result = await session.execute(comment_to_delete_stmt)
    if not comment_record_result.fetchone():
        raise HTTPException(status_code=404, detail="Коментар не знайдено або він не належить цьому стартапу.")

    delete_stmt = comment.delete().where(comment.c.id == comment_id)
    await session.execute(delete_stmt)
    await session.commit()
    return