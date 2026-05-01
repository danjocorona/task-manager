# database.py
# Handles the database engine and session lifecycle.
#
# In production (Railway), reads DATABASE_URL from environment variables
# which points to the PostgreSQL instance Railway provides.
#
# In local development, falls back to SQLite for zero-config setup.

import os
from sqlmodel import SQLModel, create_engine, Session

# Railway automatically sets DATABASE_URL when you add a PostgreSQL database.
# Locally this will be None so we fall back to SQLite.
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Railway gives a postgres:// URL but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    connect_args = {}  # PostgreSQL doesn't need check_same_thread
else:
    # Local development — use SQLite
    DATABASE_URL = "sqlite:///./taskmanager.db"
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True to print SQL queries while debugging
)


def create_db_and_tables():
    """
    Creates all database tables defined by SQLModel models.
    Called once on application startup in main.py.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency — yields a database session per request
    and guarantees it closes afterwards, even if an error occurs.
    """
    with Session(engine) as session:
        yield session