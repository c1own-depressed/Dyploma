from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from auth.auth import auth_backend
from auth.database import get_async_session, User
from auth.manager import get_user_manager
from fastapi_users import FastAPIUsers

from models.models import task, chat, rating, comment

from pydantic import BaseModel

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Pydantic-схема для оновлення
class TaskUpdateRequest(BaseModel):
    title: str
    description: str

# Pydantic-схема для відповіді
class TaskEditResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str

    class Config:
        orm_mode = True

@router.get("/task/{task_id}", response_model=TaskEditResponse)
async def get_task_by_id(
    task_id: int,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(task).where(task.c.id == task_id, task.c.customer_id == user.id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено або немає доступу")
    t = row._mapping
    return TaskEditResponse(id=t["id"], title=t["title"], description=t["description"], status=t["status"])

@router.put("/task/{task_id}", response_model=TaskEditResponse)
async def update_task_by_id(
    task_id: int,
    data: TaskUpdateRequest,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(task).where(task.c.id == task_id, task.c.customer_id == user.id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено або немає доступу")

    await session.execute(
        update(task)
        .where(task.c.id == task_id)
        .values(title=data.title, description=data.description)  # не оновлюємо статус
    )
    await session.commit()

    return TaskEditResponse(id=task_id, title=data.title, description=data.description, status=row._mapping["status"])


@router.delete("/task/{task_id}")
async def delete_task_by_id(task_id: int, session: AsyncSession = Depends(get_async_session)):
    # Перевірка наявності завдання
    result = await session.execute(select(task).where(task.c.id == task_id))  # тут замінимо task_id на id
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    # Видалення з чату та рейтингу, а також самого завдання
    await session.execute(delete(chat).where(chat.c.task_id == task_id))  # перевірте назву стовпця task_id
    await session.execute(delete(rating).where(rating.c.task_id == task_id))  # те саме тут
    await session.execute(delete(task).where(task.c.id == task_id))  # id замість task_id

    await session.commit()
    return {"status": "Завдання та всі пов'язані дані видалені"}





