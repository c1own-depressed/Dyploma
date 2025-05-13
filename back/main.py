import os
from datetime import datetime

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, update
from fastapi_users import fastapi_users, FastAPIUsers
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import current_user

from auth import database
from auth.auth import auth_backend
from auth.database import User, async_session_maker, engine
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from routes.startups import router as startup_router
from routes import tasks
from routes.profile import router as profile_router
from routes.createstartup import router as create_startup_router
from routes.createtask import router as create_task_router
from routes.editstartup import router as edit_startup_router
from routes.edittask import router as edit_task_router
from routes.completetask import router as complete_task_router
from routes.taskresult import router as result_task_router
from routes.chats import router as chats_router
from routes.auth_actions import router as auth_actions_router

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app = FastAPI(
    title="My App"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(startup_router)
app.include_router(tasks.router)
app.include_router(profile_router, tags=["user"])
app.include_router(create_startup_router)
app.include_router(create_task_router)
app.include_router(edit_startup_router)
app.include_router(edit_task_router)
app.include_router(complete_task_router)
app.include_router(result_task_router)
app.include_router(chats_router)
app.include_router(auth_actions_router)