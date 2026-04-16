from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Shared enums ──────────────────────────────────────────────────────────────

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


# ── USER_PROFILE store ────────────────────────────────────────────────────────
# Structured identity data. NEVER stored as a note.
# Retrieval is always deterministic — no LLM inference.

class UserProfile(BaseModel):
    full_name: str = ""
    preferred_name: str = ""
    email: str = ""
    timezone: str = ""
    extras: dict[str, str] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Known profile keys — updates to these go to named fields, not extras
    _KNOWN_KEYS: set[str] = {"full_name", "preferred_name", "email", "timezone"}

    def get_field(self, key: str) -> str | None:
        """Deterministic lookup — no inference, no fallback to LLM."""
        normalised = key.lower().replace(" ", "_")
        if normalised in self._KNOWN_KEYS:
            val = getattr(self, normalised, "")
            return val if val else None
        return self.extras.get(normalised) or None

    def set_field(self, key: str, value: str) -> None:
        normalised = key.lower().replace(" ", "_")
        if normalised in self._KNOWN_KEYS:
            setattr(self, normalised, value)
        else:
            self.extras[normalised] = value
        self.updated_at = datetime.now().isoformat()

    def display_name(self) -> str:
        return self.preferred_name or self.full_name or "unknown"

    def is_empty(self) -> bool:
        return not any([self.full_name, self.preferred_name, self.email, self.timezone, self.extras])


# ── NOTES store ───────────────────────────────────────────────────────────────
# Lightweight, unstructured memory entries — ideas, observations, reminders.
# Not for identity data, not for tasks.

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ── TASKS store ───────────────────────────────────────────────────────────────

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None

    def complete(self) -> None:
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now().isoformat()

    def update_fields(self, **kwargs) -> None:
        """Apply partial updates. Only known fields are accepted."""
        allowed = {"title", "description", "priority", "status", "due_date"}
        for key, value in kwargs.items():
            if key in allowed and value is not None:
                setattr(self, key, value)


class Preferences(BaseModel):
    work_start: str = "09:00"
    work_end: str = "18:00"
    focus_block_minutes: int = 90
    break_minutes: int = 15
    extras: dict[str, str] = Field(default_factory=dict)


class TaskStore(BaseModel):
    tasks: list[Task] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)
