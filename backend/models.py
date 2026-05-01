# models.py
# Defines the database tables and the Pydantic schemas used for
# request validation and response serialization — all in one place
# using SQLModel, which merges SQLAlchemy models with Pydantic models.

from datetime import date
from typing import Optional
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship

# ───────────────────────── ENUMS ──────────────────────────────
# These restrict the allowed values for priority and status fields
# both at the API (Pydantic validation) and DB (stored as strings) level.

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

# ──────────────────────── USER MODELS ─────────────────────────

class UserBase(SQLModel):
    """Fields shared across User schemas."""
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(index=True, unique=True)

class User(UserBase, table=True):
    """
    The actual database table (table=True).
    Stores the hashed password - the plain text password is NEVER stored.
    Has a one-to-many relationship to Task.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    # Relationship - access user.task to get all tasks for this user
    tasks: list["Task"] = Relationship(back_populates="owner")

class UserCreate(UserBase):
    """Request body schema for POST /aut/register."""
    password: str = Field(min_length=6)

class UserRead(UserBase):
    """Response schema - never exposes the hashed password."""
    id: int

# ──────────────────────── TASK MODELS ─────────────────────────

class TaskBase(SQLModel):
    """Fields shared across Task schemas."""
    title: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    due_date: Optional[date] = None
    priority: Priority = Field(default=Priority.medium)
    status: Status = Field(default=Status.todo)

class Task(TaskBase, table=True):
    """
    The actual database table for tasks.
    Each task belongs to one User via owner_id (foreign key).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Relationship - access task.owner to get the User who owns this task
    owner: Optional[User] = Relationship(back_populates="tasks")

class TaskCreate(TaskBase):
    """Request body schema for POST /tasks."""
    pass    # Inherits all fields from TaskBase - owner_id comes from the JWT token

class TaskUpdate(SQLModel):
    """
    Request body schema for PATCH /task/{id}.
    Every field is Optional so the client can update only what changed
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    due_date: Optional[date] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None

class TaskRead(TaskBase):
    """Response schema for task endpoints."""
    id: int
    owner_id: int