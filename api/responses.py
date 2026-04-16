"""
Response builders — all engine output goes through these helpers.

Every function returns a ChatResponse. No raw dicts escape the engine.
Typed builders encode domain knowledge: which actions belong on which response,
what data shapes each type carries, and what UI hints the frontend needs.
"""
from __future__ import annotations

from typing import Any

from core.types import ChatResponse, Action


# ── Generic builders ──────────────────────────────────────────────────────────

def build_response(
    type: str,
    message: str,
    data: dict[str, Any] | None = None,
    actions: list[Action] | None = None,
    ui: dict[str, Any] | None = None,
) -> ChatResponse:
    return ChatResponse(
        type=type,
        message=message,
        data=data or {},
        actions=actions or [],
        ui=ui or {},
    )


def chat(message: str) -> ChatResponse:
    return ChatResponse(message=message, type="chat")


def error(message: str) -> ChatResponse:
    return ChatResponse(message=message, type="error")


def awaiting_input(message: str, missing_fields: list[str]) -> ChatResponse:
    return ChatResponse(
        message=message,
        type="awaiting_input",
        data={"missing_fields": missing_fields},
    )


# ── Task builders ─────────────────────────────────────────────────────────────

def task_created(message: str, task) -> ChatResponse:
    return ChatResponse(
        message=message,
        type="action_result",
        data={"tasks": [_fmt_task(task)]},
        actions=[
            Action(id="view_tasks", type="list_tasks", label="View all tasks", payload={}),
        ],
        ui={"highlight_task_id": task.id},
    )


def task_updated(message: str, task_id: str, changes: dict) -> ChatResponse:
    return ChatResponse(
        message=message,
        type="action_result",
        data={"meta": {"task_id": task_id, "changes": changes}},
        ui={"highlight_task_id": task_id},
    )


def task_list(message: str, tasks: list) -> ChatResponse:
    return ChatResponse(
        message=message,
        type="action_result",
        data={"tasks": [_fmt_task(t) for t in tasks]},
    )


def confirmation(
    message: str,
    action: str,
    task_id: str | None = None,
    payload: dict | None = None,
) -> ChatResponse:
    """
    Presents the user with a yes/no choice.

    'Yes' action sends type=action with the full payload to /action.
    'No' action sends type='cancel' which is a no-op.
    """
    confirm_payload: dict[str, Any] = payload or {}
    if task_id:
        confirm_payload = {"task_id": task_id, **confirm_payload}

    return ChatResponse(
        message=message,
        type="confirmation",
        actions=[
            Action(
                id="confirm",
                type=action,
                label="Yes, do it",
                payload=confirm_payload,
            ),
            Action(
                id="cancel",
                type="cancel",
                label="No, cancel",
                payload={},
            ),
        ],
        ui={"show_confirmation": True},
    )


# ── Private helpers ───────────────────────────────────────────────────────────

def _fmt_task(task) -> dict:
    return {
        "id":          task.id,
        "title":       task.title,
        "priority":    task.priority.value if hasattr(task.priority, "value") else str(task.priority),
        "status":      task.status.value   if hasattr(task.status,   "value") else str(task.status),
        "due_date":    task.due_date,
        "description": task.description,
    }
