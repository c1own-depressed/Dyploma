from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from auth.auth import auth_backend
from auth.database import get_async_session, User
from auth.manager import get_user_manager
from models.models import task, user as user_table, chat  # <=== уникаємо конфлікту назв

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

class TaskDetailSchema(BaseModel):
    id: int
    title: str
    description: str
    created_at: str
    status: str
    owner_name: Optional[str]


# Отримати одну задачу по ID
@router.get("/{task_id}", response_model=TaskDetailSchema)
async def get_task(task_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(
            task.c.id,
            task.c.title,
            task.c.description,
            task.c.created_at,
            task.c.status,
            user_table.c.username.label("owner_name")
        ).join(user_table, user_table.c.id == task.c.customer_id)
        .where(task.c.id == task_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    row_dict = {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "created_at": row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "status": row.status,
        "owner_name": row.owner_name
    }
    return TaskDetailSchema(**row_dict)


# Отримати список усіх задач
@router.get("/", response_model=List[TaskDetailSchema])
async def list_tasks(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(
            task.c.id,
            task.c.title,
            task.c.description,
            task.c.created_at,
            task.c.status,
            user_table.c.username.label("owner_name")
        ).join(user_table, user_table.c.id == task.c.customer_id)
    )
    rows = result.fetchall()

    task_list = []
    for row in rows:
        row_dict = {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "created_at": row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "status": row.status,
            "owner_name": row.owner_name
        }
        task_list.append(TaskDetailSchema(**row_dict))

    return task_list


# FastAPI Users setup
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Взяти таску
@router.post("/{task_id}/take")
async def take_task(
    task_id: int,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(task).where(task.c.id == task_id))
    task_row = result.first()

    if not task_row:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_row.status == "in_progress":
        raise HTTPException(status_code=400, detail="Task is already in progress")

    stmt = (
        update(task)
        .where(task.c.id == task_id)
        .values(status="in_progress", executor_id=user.id)
        .execution_options(synchronize_session="fetch")
    )
    await session.execute(stmt)
    await session.commit()

    result_user = await session.execute(
        select(user_table.c.username).where(user_table.c.id == user.id)
    )
    user_row = result_user.first()

    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Task successfully taken", "executor_name": user_row.username}
