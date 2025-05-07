# schemas/task_schemas.py
from pydantic import BaseModel
from datetime import datetime


class TaskCreateSchema(BaseModel):
    title: str
    description: str
    startup_id: int


class TaskDetailSchema(TaskCreateSchema):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# routers/create_task.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from auth.auth import auth_backend
from auth.manager import get_user_manager
from fastapi_users import FastAPIUsers
from auth.database import get_async_session, User
from models.models import task, startup  # таблиці з БД


router = APIRouter(
    prefix="/create_task",
    tags=["create_task"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

@router.post("/", response_model=TaskDetailSchema)
async def create_task(
        task_data: TaskCreateSchema,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(startup).where(startup.c.id == task_data.startup_id))
    target_startup = result.first()

    if not target_startup:
        raise HTTPException(status_code=404, detail="Стартап не знайдено")

    new_task = task.insert().values(
        title=task_data.title,
        description=task_data.description,
        created_at=datetime.utcnow(),
        startup_id=task_data.startup_id,
        customer_id=user.id  # обов’язково використовувати правильне поле
    )

    await session.execute(new_task)
    await session.commit()

    result = await session.execute(
        select(task.c.id, task.c.title, task.c.description, task.c.startup_id, task.c.created_at)
        .where(task.c.title == task_data.title, task.c.startup_id == task_data.startup_id)
    )
    task_row = result.first()

    if not task_row:
        raise HTTPException(status_code=500, detail="Не вдалося створити завдання")

    return {
        "id": task_row.id,
        "title": task_row.title,
        "description": task_row.description,
        "startup_id": task_row.startup_id,
        "created_at": task_row.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
