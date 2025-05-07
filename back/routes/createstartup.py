from fastapi_users import FastAPIUsers
from pydantic import BaseModel

from auth.auth import auth_backend
from auth.manager import get_user_manager


class StartupCreateSchema(BaseModel):
    name: str
    description: str

class StartupDetailSchema(StartupCreateSchema):
    id: int
    created_at: str

from auth.database import get_async_session, User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from models.models import startup, user as user_table  # імпортуємо модель стартапу

# Змінили префікс роутера на '/create_startup', щоб уникнути конфлікту
router = APIRouter(
    prefix="/create_startup",  # новий префікс
    tags=["create_startup"]  # тег для роутера
)
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Створити стартап
@router.post("/", response_model=StartupDetailSchema)
async def create_startup(
        startup_data: StartupCreateSchema,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    # Перевірка чи стартап з такою назвою вже існує
    result = await session.execute(select(startup).where(startup.c.name == startup_data.name))
    existing_startup = result.first()

    if existing_startup:
        raise HTTPException(status_code=400, detail="Стартап з такою назвою вже існує")


    # Замість явної вставки значення id:
    new_startup = startup.insert().values(
        name=startup_data.name,
        description=startup_data.description,
        created_at=datetime.utcnow(),
        owner_id=user.id  # Призначаємо користувача як власника стартапу
    )

    # Виконання запиту
    await session.execute(new_startup)
    await session.commit()

    # Отримуємо дані для відповіді
    result = await session.execute(
        select(startup.c.id, startup.c.name, startup.c.description, startup.c.created_at)
        .where(startup.c.name == startup_data.name)
    )
    startup_row = result.first()

    if not startup_row:
        raise HTTPException(status_code=500, detail="Не вдалося створити стартап")

    # Повертаємо створений стартап
    return {
        "id": startup_row.id,
        "name": startup_row.name,
        "description": startup_row.description,
        "created_at": startup_row.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
