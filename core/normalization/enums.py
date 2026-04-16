"""
Enum Normalization — coerce raw LLM string output to typed enum values.

The LLM returns strings like "high", "HIGH", "in_progress", "IN_PROGRESS".
These must be normalized to enum members before they touch the data layer.

Inject in engine BEFORE operation creation so every downstream handler
receives clean enum values, not raw strings.
"""
from __future__ import annotations

from memory.models import Priority, TaskStatus


def normalize_priority(value: str | None) -> Priority | None:
    """Coerce "high" / "HIGH" → Priority.HIGH. Returns None if blank or unrecognised."""
    if not value:
        return None
    cleaned = value.strip().lower()
    try:
        return Priority(cleaned)           # matches by value: "high" → HIGH
    except ValueError:
        pass
    try:
        return Priority[value.strip().upper()]   # matches by name: "HIGH" → HIGH
    except KeyError:
        return None


def normalize_status(value: str | None) -> TaskStatus | None:
    """Coerce "done" / "IN_PROGRESS" → TaskStatus enum. Returns None if blank."""
    if not value:
        return None
    cleaned = value.strip().lower()
    try:
        return TaskStatus(cleaned)
    except ValueError:
        pass
    try:
        return TaskStatus[value.strip().upper()]
    except KeyError:
        return None


def normalize_intent_params(params: dict) -> dict:
    """
    Run all enum normalizations on an intent's parameter dict in-place.
    Safe to call on any intent — skips fields that are absent or already correct.
    """
    if "priority" in params and params["priority"]:
        coerced = normalize_priority(params["priority"])
        if coerced:
            params["priority"] = coerced

    if "status" in params and params["status"]:
        coerced = normalize_status(params["status"])
        if coerced:
            params["status"] = coerced

    return params
