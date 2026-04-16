from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class IntentType(str, Enum):
    PLAN_DAY = "plan_day"
    REFLECT = "reflect"
    ADD_TASK = "add_task"
    UPDATE_TASK = "update_task"
    LIST_TASKS = "list_tasks"
    COMPLETE_TASK = "complete_task"
    REMOVE_TASK = "remove_task"
    ADD_NOTE = "add_note"
    # Identity — explicitly separate from notes (see memory-overload-and-identity-design.md)
    UPDATE_PROFILE = "update_profile"
    GET_PROFILE = "get_profile"
    # File system — explicitly separate from notes (see intent-collapse-file-vs-note.md)
    CREATE_FILE = "create_file"
    READ_FILE = "read_file"
    UPDATE_FILE = "update_file"
    GENERAL_CHAT = "general_chat"


class IntentResult(BaseModel):
    intent: IntentType
    parameters: dict[str, Any] = {}

    def __str__(self) -> str:
        return f"IntentResult(intent={self.intent}, parameters={self.parameters})"
