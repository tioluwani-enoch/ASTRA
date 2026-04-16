"""
Confirmation Resolver — detects user affirmatives and routes to pending actions.

Detection is intentionally narrow: a closed set of short affirmatives.
Longer user messages are passed through to normal intent parsing so the
resolver never swallows a legitimate new command.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.conversation.memory import ConversationMemory
    from core.conversation.models import PendingAction

CONFIRM_WORDS: frozenset[str] = frozenset({
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay",
    "do it", "go ahead", "please do", "correct", "right",
    "exactly", "aye", "definitely", "absolutely", "sounds good",
})


def is_confirmation(message: str) -> bool:
    """True if the message is an unambiguous short affirmative."""
    return message.strip().lower().rstrip("!.") in CONFIRM_WORDS


def resolve_confirmation(
    memory: ConversationMemory,
    message: str,
) -> PendingAction | None:
    """
    Return the pending action if the message confirms it, otherwise None.

    Caller is responsible for calling memory.clear() after consuming the action.
    """
    if memory.state.awaiting_confirmation and is_confirmation(message):
        return memory.state.pending_action
    return None
