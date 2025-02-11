from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from app.models import (
    Task,
    TaskCreate,
    TaskRead,
    TaskStatus,
    TaskUpdate,
    get_next_interval,
)
from app.settings import settings
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, SQLModel, create_engine, select
import uvicorn

engine = create_engine(settings.sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
api = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:9000", "https://localhost:9000", "https://lcr.chiggydoes.tech"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SessionDep = Annotated[Session, Depends(get_session)]


@api.get("/tasks", response_model=list[TaskRead])
async def read_tasks(session: SessionDep):
    """Get Tasks"""
    tasks = session.exec(select(Task)).all()
    return tasks


@api.get("/tasks/today", response_model=list[TaskRead])
def get_todays_tasks(session: SessionDep):
    """Retrieve tasks that are due today."""
    today = date.today()
    tasks = session.exec(select(Task).where(Task.due_date >= today, Task.due_date < today + timedelta(days=1))).all()
    return tasks


@api.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, session: SessionDep):
    """Retrieve a specific task by ID."""
    task = session.exec(select(Task).where(Task.id == task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@api.post("/tasks", response_model=TaskRead)
def create_task(task: TaskCreate, session: SessionDep):
    """Create a new task."""
    new_task = Task(**task.model_dump(), repeat_interval=1, status=TaskStatus.PENDING)
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task


@api.put("/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(task_id: int, session: SessionDep):
    """Marks a task as completed and schedules the next occurrence if applicable."""

    task = session.exec(select(Task).where(Task.id == task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.COMPLETED
    session.add(task)

    next_interval = get_next_interval(task.repeat_interval)
    if next_interval:
        new_task = Task(
            title=task.title,
            description=task.description,
            due_date=datetime.now(timezone.utc) + timedelta(days=next_interval),
            repeat_interval=next_interval,
        )
        session.add(new_task)

    session.commit()
    return task


@api.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int, session: SessionDep):
    """Delete a task."""
    task = session.exec(select(Task).where(Task.id == task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()

    return {"message": "Task deleted successfully"}


app.include_router(api)
