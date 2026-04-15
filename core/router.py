from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    PLAN = "plan"
    TASK = "task"
    REFLECT = "reflect"
    NOTE = "note"
    UNKNOWN = "unknown"


_KEYWORDS: dict[Intent, list[str]] = {
    Intent.PLAN: ["plan", "schedule", "day", "agenda", "organize my day"],
    Intent.TASK: ["task", "add task", "remove task", "list tasks", "complete task", "finish", "todo"],
    Intent.REFLECT: ["reflect", "reflection", "review", "end of day", "how did i do"],
    Intent.NOTE: ["note", "remember", "jot", "write down"],
}


def route(user_input: str) -> Intent:
    lower = user_input.lower()
    for intent, keywords in _KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return intent
    return Intent.UNKNOWN
