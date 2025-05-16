# У вашому файлі з роутером /user (наприклад, user.py або main.py)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import FileResponse  # Додано для відправки файлів
import os  # Додано для роботи зі шляхами

from auth.manager import get_user_manager
from models.models import task, rating  # Переконайтесь, що модель task імпортована
from pydantic import BaseModel
from auth.database import get_async_session, User  # Переконайтесь, що User імпортований
from auth.auth import auth_backend  # Переконайтесь, що auth_backend імпортований
from fastapi_users import FastAPIUsers
from typing import Optional  # Додано для Optional полів

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Директорія, де зберігаються завантажені файли виконавцями
# Вона має бути такою ж, як і при завантаженні файлу
UPLOAD_DIR = "static/task_files"


# Pydantic модель TaskResultResponse
class TaskResultResponse(BaseModel):
    id: int
    title: str
    description: str
    executionResult: str
    attachedFileName: Optional[str] = None
    isRatedByCustomer: bool = False # Нове поле, за замовчуванням false

    class Config:
        from_attributes = True


# Схема для оцінки (залишається без змін)
class RatingRequest(BaseModel):
    rating: int


@router.get("/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(
        task_id: int,
        session: AsyncSession = Depends(get_async_session),
        # Якщо для визначення isRatedByCustomer потрібен поточний користувач,
        # його потрібно тут отримати.
        # Припустимо, логіка така: якщо завдання існує і для нього є оцінка,
        # то це оцінка від замовника.
        # user: User = Depends(fastapi_users.current_user(optional=True)) # Можливо, потрібен для перевірки, чи поточний юзер = customer
):
    result_db = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    task_row = result_db.fetchone()

    if not task_row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    task_data = task_row._mapping

    is_rated = False
    # Перевіряємо, чи є оцінка для цього завдання
    # Ця логіка спрацює коректно, якщо тільки замовник може оцінювати своє завдання,
    # і він може це зробити лише один раз.
    existing_rating_query = select(rating.c.id).where(rating.c.task_id == task_id) # Просто перевіряємо наявність
    existing_rating_result = await session.execute(existing_rating_query)
    if existing_rating_result.fetchone():
        is_rated = True

    file_name = None
    if task_data.get("execution_image"):
        try:
            file_name = os.path.basename(task_data["execution_image"])
        except Exception:
            file_name = None

    return TaskResultResponse(
        id=task_data["id"],
        title=task_data["title"],
        description=task_data["description"],
        executionResult=task_data["execution_description"] or "Опис виконання відсутній.",
        attachedFileName=file_name,
        isRatedByCustomer=is_rated # Додаємо нове поле у відповідь
    )


# Новий ендпоінт для завантаження файлу, прикріпленого до завдання
@router.get("/download_attachment/{filename}")
async def download_task_attachment(filename: str):
    # Базовий захист від path traversal атак
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        raise HTTPException(status_code=400, detail="Некоректне ім'я файлу.")

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Файл не знайдено на сервері.")

    # FileResponse автоматично встановлює відповідні Content-Type на основі розширення файлу
    # і Content-Disposition для завантаження
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')


@router.post("/{task_id}/rate")
async def submit_rating(
        task_id: int,
        rating_request: RatingRequest,
        user: User = Depends(fastapi_users.current_user()),
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(task).where(task.c.id == task_id))
    task_row = result.fetchone()
    if not task_row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    task_data = task_row._mapping
    executor_id = task_data.get("executor_id")
    customer_id_from_task = task_data.get("customer_id") # Отримуємо customer_id з завдання

    if executor_id is None:
        raise HTTPException(status_code=400, detail="Завдання не має виконавця, щоб його оцінити.")

    # Перевірка, чи поточний користувач є замовником цього завдання (ця перевірка залишається важливою!)
    if customer_id_from_task != user.id:
        raise HTTPException(status_code=403, detail="Ви не можете оцінити це завдання, оскільки не є його замовником.")

    # ЗМІНЕНА Перевірка, чи завдання вже було оцінене (замовником)
    # Оскільки тільки замовник може оцінити, перевіряємо, чи існує хоча б одна оцінка для цього task_id
    existing_rating_query = select(rating).where(rating.c.task_id == task_id)
    existing_rating_result = await session.execute(existing_rating_query)
    if existing_rating_result.fetchone():
        raise HTTPException(status_code=400, detail="Ви вже оцінили це завдання.") # Або "Це завдання вже було оцінене."

    if not (1 <= rating_request.rating <= 5):
        raise HTTPException(status_code=400, detail="Оцінка повинна бути від 1 до 5.")

    # ЗМІНЕНЕ Збереження оцінки без customer_id
    new_rating_stmt = rating.insert().values(
        rating=rating_request.rating,
        task_id=task_id,
        executor_id=executor_id
        # comment=rating_request.comment, # Якщо у вас є поле comment у RatingRequest та в таблиці rating
    )
    await session.execute(new_rating_stmt)
    await session.commit()

    return {"message": "Оцінка успішно подана"}