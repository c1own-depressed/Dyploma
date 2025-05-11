# file: routers/auth_actions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from datetime import datetime # Потрібно, якщо будете використовувати datetime.min

# Переконайтеся, що User - це Pydantic модель, а user_table - SQLAlchemy таблиця
from auth.database import get_async_session, User
from models.models import user as user_table

# Імпортуйте ваш FastAPIUsers інстанс або його компоненти
from auth.manager import get_user_manager
from auth.auth import auth_backend
from fastapi_users import FastAPIUsers

# Ініціалізація FastAPIUsers для цього роутера
# (якщо у вас немає глобального інстансу, який можна імпортувати)
logout_fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

router = APIRouter(
    prefix="/auth-actions", # Префікс для цих дій
    tags=["Auth Actions"]    # Тег для Swagger документації
)

@router.post("/logout_explicit")
async def logout_explicit_action(
    # Використовуємо залежність current_user від FastAPIUsers
    # Важливо НЕ використовувати тут get_current_active_user_and_update_last_seen,
    # оскільки це перезапише last_seen на поточний час.
    current_user: User = Depends(logout_fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session)
):
    if not current_user:
        # Цього не повинно статися, якщо залежність current_user працює коректно
        raise HTTPException(status_code=401, detail="Not authenticated")

    stmt = (
        update(user_table)
        .where(user_table.c.id == current_user.id)
        .values(last_seen=None) # Встановлюємо last_seen в None, щоб позначити як офлайн
                                # Альтернатива: datetime.min (потребує import datetime)
    )
    await session.execute(stmt)
    await session.commit()
    return {"message": "User marked as offline successfully"}