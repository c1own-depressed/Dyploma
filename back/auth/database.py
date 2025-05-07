from datetime import datetime
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker

from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER
from models.models import role

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base: DeclarativeMeta = declarative_base()

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    username = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    role_id = Column(Integer, ForeignKey(role.c.id))
    hashed_password = Column(String(1024), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

class Startup(Base):
    __tablename__ = "startups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("user.id"))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    startup_id = Column(Integer, ForeignKey("startups.id"))
    customer_id = Column(Integer, ForeignKey("user.id"))
    executor_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    execution_description = Column(Text, nullable=True)
    execution_image = Column(String, nullable=True)

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    executor_id = Column(Integer, ForeignKey("user.id"))

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("user.id"))
    startup_id = Column(Integer, ForeignKey("startups.id"))

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
