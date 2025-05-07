from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth.manager import get_user_manager
from models.models import task, rating
from pydantic import BaseModel
from auth.database import get_async_session, User
from auth.auth import auth_backend
from fastapi_users import FastAPIUsers

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


# Схема для результату завдання
class TaskResultResponse(BaseModel):
    id: int
    title: str
    description: str
    executionResult: str

    class Config:
        orm_mode = True


# Схема для оцінки
class RatingRequest(BaseModel):
    rating: int


@router.get("/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(
        task_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    # Перевірка чи існує завдання
    result = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    task_data = row._mapping
    return TaskResultResponse(
        id=task_data["id"],
        title=task_data["title"],
        description=task_data["description"],
        executionResult=task_data["execution_description"] or "Немає результату"
    )


@router.post("/{task_id}/rate")
async def submit_rating(
        task_id: int,
        rating_request: RatingRequest,
        session: AsyncSession = Depends(get_async_session)
):
    # Перевірка чи завдання існує та отримання виконавця
    result = await session.execute(select(task).where(task.c.id == task_id))
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    task_data = row._mapping
    executor_id = task_data["executor_id"]
    if executor_id is None:
        raise HTTPException(status_code=400, detail="Завдання не має виконавця")

    # Додавання оцінки в базу
    new_rating = rating.insert().values(
        rating=rating_request.rating,
        task_id=task_id,
        executor_id=executor_id
    )
    await session.execute(new_rating)
    await session.commit()

    return {"status": "Оцінка подана успішно"}
