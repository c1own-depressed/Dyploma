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


# Оновлена схема для результату завдання
class TaskResultResponse(BaseModel):
    id: int
    title: str
    description: str
    executionResult: str  # Це task.c.execution_description
    attachedFileName: Optional[str] = None  # Ім'я прикріпленого файлу, наприклад, "report.pdf"

    class Config:
        from_attributes = True  # Для Pydantic v2 (замініть orm_mode = True, якщо у вас Pydantic v1)


# Схема для оцінки (залишається без змін)
class RatingRequest(BaseModel):
    rating: int


@router.get("/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(
        task_id: int,
        session: AsyncSession = Depends(get_async_session),
        # user: User = Depends(fastapi_users.current_user()) # Розкоментуйте, якщо потрібна автентифікація для цього ендпоінту
):
    # Перевірка чи існує завдання
    result_db = await session.execute(
        select(task).where(task.c.id == task_id)
    )
    task_row = result_db.fetchone()  # Використовуємо fetchone, оскільки очікуємо один запис або жодного

    if not task_row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    task_data = task_row._mapping  # Доступ до даних як до словника

    file_name = None
    # task.c.execution_image зберігає відносний шлях до файлу, наприклад 'static/task_files/filename.ext'
    if task_data.get("execution_image"):
        try:
            # Витягуємо тільки ім'я файлу зі шляху
            file_name = os.path.basename(task_data["execution_image"])
        except Exception:
            # Можна додати логування помилки, якщо шлях некоректний
            file_name = None

    return TaskResultResponse(
        id=task_data["id"],
        title=task_data["title"],
        description=task_data["description"],
        executionResult=task_data["execution_description"] or "Опис виконання відсутній.",
        attachedFileName=file_name
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
        user: User = Depends(fastapi_users.current_user()),  # Додано користувача для отримання customer_id
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(task).where(task.c.id == task_id))
    task_row = result.fetchone()
    if not task_row:
        raise HTTPException(status_code=404, detail="Завдання не знайдено")

    task_data = task_row._mapping
    executor_id = task_data.get("executor_id")
    customer_id = task_data.get("customer_id")  # Отримуємо customer_id з завдання

    if executor_id is None:
        raise HTTPException(status_code=400, detail="Завдання не має виконавця, щоб його оцінити.")

    # Перевірка, чи поточний користувач є замовником цього завдання
    if customer_id != user.id:
        raise HTTPException(status_code=403, detail="Ви не можете оцінити це завдання, оскільки не є його замовником.")

    # Перевірка, чи завдання вже було оцінене
    existing_rating_result = await session.execute(
        select(rating).where(rating.c.task_id == task_id).where(rating.c.customer_id == user.id)
    )
    if existing_rating_result.fetchone():
        raise HTTPException(status_code=400, detail="Ви вже оцінили це завдання.")

    if not (1 <= rating_request.rating <= 5):
        raise HTTPException(status_code=400, detail="Оцінка повинна бути від 1 до 5.")

    new_rating_stmt = rating.insert().values(
        rating=rating_request.rating,
        task_id=task_id,
        executor_id=executor_id,
        customer_id=user.id  # Зберігаємо ID користувача, який поставив оцінку (замовника)
    )
    await session.execute(new_rating_stmt)
    await session.commit()

    return {"message": "Оцінка успішно подана"}