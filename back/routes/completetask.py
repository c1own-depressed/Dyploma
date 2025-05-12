from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import shutil  # Для збереження файлів
import os  # Для роботи з шляхами
from typing import Optional  # Для опціонального файлу

from auth.manager import get_user_manager
from models.models import task  # імпортуємо модель завдання
# Pydantic schema більше не потрібна для тіла запиту, оскільки ми використовуємо Form
# from pydantic import BaseModel
from auth.database import get_async_session, User
from auth.auth import auth_backend
from fastapi_users import FastAPIUsers

# Створимо директорію для завантажених файлів, якщо її немає
UPLOAD_DIR = "static/task_files"
# Важливо: переконайтеся, що ваш FastAPI додаток може сервірувати статичні файли,
# якщо ви плануєте надавати до них прямий доступ через URL.
# Наприклад, додавши в main.py: app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


@router.post("/{task_id}/complete")
async def complete_task(
        task_id: int,
        execution_description: str = Form(...),  # Опис тепер отримуємо з Form
        file: Optional[UploadFile] = File(None),  # Файл тепер опціональний
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

    # Перевірка, чи завдання вже не виконане
    if task_row.status == "done":
        raise HTTPException(status_code=400, detail="Завдання вже виконано")

    file_path_to_save = None  # Шлях до збереженого файлу в БД

    if file:
        # Валідація файлу (приклад)
        if file.content_type not in ["image/jpeg", "image/png", "application/pdf", "application/msword",
                                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                     "text/plain", "application/zip"]:
            raise HTTPException(status_code=400,
                                detail=f"Непідтримуваний тип файлу: {file.content_type}. Дозволені: JPEG, PNG, PDF, DOC, DOCX, TXT, ZIP.")

        # Обмеження розміру файлу (наприклад, 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        # file.file є об'єктом SpooledTemporaryFile, потрібно перевірити його розмір
        # Для цього читаємо його в пам'ять або перевіряємо headers, якщо доступно.
        # Найпростіший, але не найефективніший спосіб для великих файлів - прочитати і перевірити.
        # Більш ефективно - перевіряти 'content-length' заголовка, якщо клієнт його надсилає.
        # Або обробляти файл по частинам.

        # Спробуємо отримати розмір файлу, якщо це можливо, без повного зчитування
        size = 0
        # file.file.seek(0, os.SEEK_END)
        # size = file.file.tell()
        # file.file.seek(0) # Повертаємо курсор на початок
        # if size > MAX_FILE_SIZE:
        #     raise HTTPException(status_code=413, detail=f"Файл занадто великий. Максимальний розмір: {MAX_FILE_SIZE // (1024*1024)}MB.")
        # На жаль, UploadFile не завжди надає простий спосіб отримати розмір до читання.
        # Можна читати частинами або покластися на ліміти веб-сервера (nginx, gunicorn).

        # Генерація унікального імені файлу, щоб уникнути перезапису
        # Можна додати timestamp або UUID
        original_filename = file.filename
        filename_parts = os.path.splitext(original_filename)
        unique_filename = f"{filename_parts[0]}_{int(datetime.now().timestamp())}{filename_parts[1]}"

        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            with open(file_path, "wb") as buffer:
                # shutil.copyfileobj(file.file, buffer) # Старий варіант
                content = await file.read()  # Асинхронне читання файлу
                if len(content) > MAX_FILE_SIZE:
                    # Видаляємо частково записаний файл, якщо він був створений
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(status_code=413,
                                        detail=f"Файл занадто великий. Максимальний розмір: {MAX_FILE_SIZE // (1024 * 1024)}MB.")
                buffer.write(content)
            file_path_to_save = f"{UPLOAD_DIR}/{unique_filename}"  # Зберігаємо відносний шлях
        except Exception as e:
            # Потенційно видалити частково збережений файл, якщо щось пішло не так
            if os.path.exists(file_path):
                os.remove(file_path)
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Помилка при збереженні файлу: {e}")
        finally:
            await file.close()  # Завжди закриваємо файл

    # Оновлюємо завдання в базі даних
    try:
        values_to_update = {
            "execution_description": execution_description,
            "status": "done"
        }
        if file_path_to_save:
            # Використовуємо 'execution_image' для збереження шляху до файлу
            values_to_update["execution_image"] = file_path_to_save

        update_stmt = task.update().where(task.c.id == task_id).values(**values_to_update)

        await session.execute(update_stmt)
        await session.commit()

        return {
            "message": "Завдання успішно виконано",
            "task_id": task_id,
            "execution_description": execution_description,
            "status": "done",
            "file_path": file_path_to_save if file_path_to_save else "Файл не було прикріплено"
        }
    except Exception as e:
        await session.rollback()
        # Якщо файл було збережено, але сталася помилка з БД, його варто видалити
        if file_path_to_save and os.path.exists(file_path_to_save):
            os.remove(file_path_to_save)
        raise HTTPException(status_code=500, detail=f"Помилка при оновленні завдання в БД: {e}")