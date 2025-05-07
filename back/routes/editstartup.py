from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete


from auth.auth import auth_backend
from auth.database import get_async_session, User
from auth.manager import get_user_manager
from fastapi_users import FastAPIUsers

from models.models import startup, task, chat, rating, comment

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
class StartupUpdateRequest(BaseModel):
    name: str
    description: str

# Pydantic-схема для відповіді
class StartupEditResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True

@router.get("/startup/{startup_id}", response_model=StartupEditResponse)
async def get_startup_by_id(
    startup_id: int,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(startup).where(startup.c.id == startup_id, startup.c.owner_id == user.id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Стартап не знайдено або немає доступу")
    s = row._mapping
    return StartupEditResponse(id=s["id"], name=s["name"], description=s["description"])


@router.put("/startup/{startup_id}", response_model=StartupEditResponse)
async def update_startup_by_id(
    startup_id: int,
    data: StartupUpdateRequest,
    user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(startup).where(startup.c.id == startup_id, startup.c.owner_id == user.id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Стартап не знайдено або немає доступу")

    await session.execute(
        update(startup)
        .where(startup.c.id == startup_id)
        .values(name=data.name, description=data.description)
    )
    await session.commit()

    return StartupEditResponse(id=startup_id, name=data.name, description=data.description)


@router.delete("/startup/{startup_id}")
async def delete_startup_by_id(startup_id: int, session: AsyncSession = Depends(get_async_session)):
    # 1. Отримуємо всі task.id цього startup
    result = await session.execute(select(task.c.id).where(task.c.startup_id == startup_id))
    task_ids = [row[0] for row in result.fetchall()]

    if task_ids:
        # 2. Видаляємо чати, прив'язані до цих завдань
        await session.execute(delete(chat).where(chat.c.task_id.in_(task_ids)))

        # 3. Видаляємо оцінки, прив'язані до цих завдань
        await session.execute(delete(rating).where(rating.c.task_id.in_(task_ids)))

        # 4. Видаляємо завдання
        await session.execute(delete(task).where(task.c.id.in_(task_ids)))

    # 5. Видаляємо коментарі до стартапу
    await session.execute(delete(comment).where(comment.c.startup_id == startup_id))

    # 6. Нарешті, видаляємо сам стартап
    await session.execute(delete(startup).where(startup.c.id == startup_id))

    await session.commit()
    return {"status": "Startup and all related data deleted"}