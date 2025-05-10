from datetime import datetime

from sqlalchemy import MetaData, Table, Column, Integer, String, JSON, TIMESTAMP, ForeignKey, Boolean, Text

metadata = MetaData()
role = Table(
    "role",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("permissions", JSON),
)

user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False),
    Column("username", String, nullable=False),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
    Column("role_id", Integer, ForeignKey(role.c.id)),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_superuser", Boolean, default=False, nullable=False),
    Column("is_verified", Boolean, default=False, nullable=False),
)
# 2. Стартап (Startup)
startup = Table(
    "startups",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("owner_id", Integer, ForeignKey("user.id")),
)

# 3. Завдання (Task)
task = Table(
    "tasks",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", String, default="pending"),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("startup_id", Integer, ForeignKey("startups.id")),
    Column("customer_id", Integer, ForeignKey("user.id")),
    Column("executor_id", Integer, ForeignKey("user.id"), nullable=True),
    Column("execution_description", Text, nullable=True),
    Column("execution_image", String, nullable=True),
)

# 4. Чат (Chat)
chat = Table(
    "chats",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("task_id", Integer, ForeignKey("tasks.id"), nullable=False),
    Column("user1_id", Integer, ForeignKey("user.id"), nullable=False),  # замовник
    Column("user2_id", Integer, ForeignKey("user.id"), nullable=False),  # виконавець
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
)

message = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("chat_id", Integer, ForeignKey("chats.id"), nullable=False),
    Column("sender_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("is_read", Boolean, default=False),
)


# 5. Оцінки (Rating)
rating = Table(
    "ratings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("rating", Integer, nullable=False),
    Column("comment", Text, nullable=True),
    Column("task_id", Integer, ForeignKey("tasks.id")),
    Column("executor_id", Integer, ForeignKey("user.id")),
)

# 6. Коментар (Comment) - Пропозиція до стартапу
comment = Table(
    "comments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", Text, nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("startup_id", Integer, ForeignKey("startups.id")),
)

