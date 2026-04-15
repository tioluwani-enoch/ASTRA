from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: str | None = None  # ISO date string, e.g. "2026-04-16"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None

    def complete(self) -> None:
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now().isoformat()


class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Preferences(BaseModel):
    work_start: str = "09:00"
    work_end: str = "18:00"
    focus_block_minutes: int = 90
    break_minutes: int = 15
    extras: dict[str, str] = Field(default_factory=dict)


class MemoryStore(BaseModel):
    tasks: list[Task] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)
