from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from auth.manager import get_user_manager
from models.models import task  # імпортуємо модель завдання
from pydantic import BaseModel
from auth.database import get_async_session, User
from auth.auth import auth_backend
from fastapi_users import FastAPIUsers

# Схема для опису виконання завдання
class TaskCompletionSchema(BaseModel):
    execution_description: str

router = APIRouter(
    prefix="/tasks",  # префікс для роутера
    tags=["tasks"]  # тег для роутера
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Завершити завдання
@router.post("/{task_id}/complete")
async def complete_task(
        task_id: int,
        task_data: TaskCompletionSchema,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    # Перевірка, чи завдання існує
    result = await session.execute(select(task).where(task.c.id == task_id))
    task_row = result.first()

    if not task_row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    # Перевірка, чи користувач є виконавцем завдання
    if task_row.executor_id != user.id:
        raise HTTPException(status_code=403, detail="Немає доступу до цього завдання")

    # Оновлюємо завдання
    try:
        # Оновлюємо опис виконання завдання та статус
        update_stmt = task.update().where(task.c.id == task_id).values(
            execution_description=task_data.execution_description,
            status="done"
        )

        await session.execute(update_stmt)
        await session.commit()

        # Повертаємо оновлене завдання
        return {
            "message": "Завдання успішно виконано",
            "task_id": task_id,
            "execution_description": task_data.execution_description,
            "status": "done"
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Помилка при оновленні завдання")

