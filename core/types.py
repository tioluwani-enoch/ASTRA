"""
Core type contracts — the canonical data shapes for engine output.

ChatResponse is the single response object that flows from engine → API → frontend.
Action represents a button/follow-up the frontend can render and the user can click.

Design rules:
  message  → ONLY what the user reads
  type     → controls frontend rendering
  actions  → structured buttons (create_task, complete_task, list_tasks, cancel, …)
  data     → structured state: tasks, profile, meta
  ui       → optional rendering hints (highlight_task_id, show_confirmation, etc.)
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class Action(BaseModel):
    """
    A clickable follow-up action surfaced alongside a response.

    id      — unique label used as a key in the frontend (e.g. "confirm_add_task")
    type    — intent name the /action endpoint will route to (e.g. "add_task")
              Use "cancel" for a no-op dismiss button.
    label   — button text shown to the user
    payload — parameters forwarded directly to the handler
    """
    id:      str
    type:    str
    label:   str
    payload: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """
    Universal response shape returned by engine.handle() and /chat.

    Every engine path returns one of these — no plain strings anywhere.
    """
    message: str
    type:    str                    = "chat"        # chat | action_result | confirmation | error | awaiting_input
    actions: list[Action]           = Field(default_factory=list)
    data:    dict[str, Any]         = Field(default_factory=dict)
    ui:      dict[str, Any]         = Field(default_factory=dict)
