# main.py
# The FastAPI application entry point.
# Defines all API routes grouped into two routers:
#   /auth  — register and login (no authentication required)
#   /tasks — full CRUD, requires a valid JWT token on every request

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import date
from typing import Optional

from database import create_db_and_tables, get_session
from models import (
    User, UserCreate, UserRead,
    Task, TaskCreate, TaskUpdate, TaskRead,
    Priority, Status
)
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)


# ─── APP SETUP ────────────────────────────────────────────────

app = FastAPI(
    title="Task Manager API",
    description="A full stack task management API built with FastAPI and SQLModel.",
    version="1.0.0"
)

# CORS — allows the frontend (running on a different port or domain)
# to make requests to this API. Restrict origins before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://danjocorona.github.io",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Creates database tables on first run if they don't exist yet."""
    create_db_and_tables()


# ─── AUTH ROUTES ──────────────────────────────────────────────

@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    """
    Register a new user account.

    - Checks that the username and email are not already taken
    - Hashes the password with bcrypt before storing
    - Returns the created user (without the password)
    """
    # Check username is not taken
    existing_username = session.exec(
        select(User).where(User.username == user_data.username)
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check email is not taken
    existing_email = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user with hashed password
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session:   Session = Depends(get_session)
):
    """
    Log in with username and password.

    Uses OAuth2PasswordRequestForm which expects form data with
    fields 'username' and 'password' — standard for OAuth2 flows.

    Returns a JWT access token the frontend stores and sends
    in the Authorization header on subsequent requests.
    """
    user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile.
    Used by the frontend to verify a stored token is still valid.
    """
    return current_user


# ─── TASK ROUTES ──────────────────────────────────────────────

@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data:    TaskCreate = ...,
    session:      Session    = Depends(get_session),
    current_user: User       = Depends(get_current_user)
):
    """
    Create a new task for the authenticated user.
    The owner_id is set from the JWT token — users can only create tasks for themselves.
    """
    task = Task(**task_data.dict(), owner_id=current_user.id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskRead])
def get_tasks(
    status_filter:   Optional[Status]   = None,
    priority_filter: Optional[Priority] = None,
    session:         Session            = Depends(get_session),
    current_user:    User               = Depends(get_current_user)
):
    """
    Get all tasks belonging to the authenticated user.

    Optional query parameters:
        ?status_filter=todo|in_progress|done
        ?priority_filter=low|medium|high

    Example: GET /tasks?status_filter=todo&priority_filter=high
    """
    query = select(Task).where(Task.owner_id == current_user.id)

    if status_filter:
        query = query.where(Task.status == status_filter)
    if priority_filter:
        query = query.where(Task.priority == priority_filter)

    return session.exec(query).all()


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id:      int,
    session:      Session = Depends(get_session),
    current_user: User    = Depends(get_current_user)
):
    """
    Get a single task by ID.
    Returns 404 if not found, 403 if it belongs to a different user.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this task")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id:      int,
    task_data:    TaskUpdate,
    session:      Session    = Depends(get_session),
    current_user: User       = Depends(get_current_user)
):
    """
    Partially update a task — only the fields provided in the request body are changed.
    Returns 404 if not found, 403 if it belongs to a different user.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")

    # Apply only the fields that were actually sent (exclude_unset=True)
    update_data = task_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id:      int,
    session:      Session = Depends(get_session),
    current_user: User    = Depends(get_current_user)
):
    """
    Delete a task permanently.
    Returns 404 if not found, 403 if it belongs to a different user.
    Returns 204 No Content on success.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")

    session.delete(task)
    session.commit()


# ─── DASHBOARD SUMMARY ROUTE ──────────────────────────────────

@app.get("/tasks/summary/dashboard")
def get_dashboard_summary(
    session:      Session = Depends(get_session),
    current_user: User    = Depends(get_current_user)
):
    """
    Returns a summary of the user's tasks for the dashboard header.
    Counts total, done, in progress, todo, and overdue tasks.
    """
    tasks = session.exec(
        select(Task).where(Task.owner_id == current_user.id)
    ).all()

    today    = date.today()
    total    = len(tasks)
    done     = sum(1 for t in tasks if t.status == Status.done)
    in_prog  = sum(1 for t in tasks if t.status == Status.in_progress)
    todo     = sum(1 for t in tasks if t.status == Status.todo)
    overdue  = sum(
        1 for t in tasks
        if t.due_date and t.due_date < today and t.status != Status.done
    )

    return {
        "total":       total,
        "done":        done,
        "in_progress": in_prog,
        "todo":        todo,
        "overdue":     overdue
    }