
from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

# SQLModel Task Schema
class TaskBase(SQLModel):
    title: str
    description: str | None = None
    due_date: datetime

class TaskCreate(TaskBase):
    pass

class TaskRead(TaskBase):
    id: int
    status: TaskStatus
    repeat_interval: int

class TaskUpdate(SQLModel):
    status: TaskStatus | None = None

class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repeat_interval: int = 1  # Default interval is 1 day
    status: TaskStatus = Field(default=TaskStatus.PENDING)

REPEAT_INTERVALS = [1, 3, 7, 14, 30]

def get_next_interval(current_interval: int) -> int | None:
    """Returns the next interval in the predefined sequence."""
    for interval in REPEAT_INTERVALS:
        if interval > current_interval:
            return interval
    return None  # No further repetition
