from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PendingAction:
    """
    A structured, executable action waiting for user confirmation.

    action    — intent name (e.g. "complete_task", "add_task")
    target_id — primary entity ID when one applies (task_id, etc.)
    payload   — all remaining parameters needed to execute the action
    """
    action: str
    target_id: Optional[str] = None
    payload: dict = field(default_factory=dict)


@dataclass
class Turn:
    """A single conversational message."""
    role: str      # "user" | "assistant"
    content: str


@dataclass
class ConversationState:
    """
    Short-term state for the current conversation session.

    last_intent            — the most recently classified intent
    pending_action         — structured action awaiting user confirmation
    awaiting_confirmation  — True while a pending_action is stored
    history                — recent turns for multi-turn chat context
    """
    last_intent: Optional[str] = None
    pending_action: Optional[PendingAction] = None
    awaiting_confirmation: bool = False
    history: list = field(default_factory=list)   # list[Turn]
