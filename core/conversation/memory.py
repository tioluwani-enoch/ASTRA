"""
ConversationMemory — in-process short-term state store.

Never persisted to disk. Resets on every process start (by design —
the spec requires short-term only). Owns the full conversation state:
pending confirmations, recent turn history, and last-seen intent.
"""
from __future__ import annotations

from collections import deque

from core.conversation.models import ConversationState, PendingAction, Turn

_MAX_HISTORY = 10   # store up to 5 user+assistant turn pairs


class ConversationMemory:
    def __init__(self) -> None:
        self.state = ConversationState()
        self._turns: deque[Turn] = deque(maxlen=_MAX_HISTORY)

    # ── Pending action ────────────────────────────────────────────────────────

    def set_pending_action(
        self,
        action: str,
        target_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        self.state.pending_action = PendingAction(
            action=action,
            target_id=target_id,
            payload=payload or {},
        )
        self.state.awaiting_confirmation = True

    def clear(self) -> None:
        self.state.pending_action = None
        self.state.awaiting_confirmation = False

    # ── Intent tracking ───────────────────────────────────────────────────────

    def set_last_intent(self, intent: str) -> None:
        self.state.last_intent = intent

    # ── Turn history (for multi-turn general_chat context) ────────────────────

    def add_turn(self, role: str, content: str) -> None:
        turn = Turn(role=role, content=content)
        self._turns.append(turn)

    def recent_summary(self) -> str:
        """Plain-text history block for injection into an LLM system prompt."""
        if not self._turns:
            return ""
        lines = []
        for t in self._turns:
            prefix = "User" if t.role == "user" else "Astra"
            lines.append(f"{prefix}: {t.content}")
        return "\n".join(lines)

    def as_messages(self) -> list[dict]:
        """Anthropic messages-list format for multi-turn chat calls."""
        return [{"role": t.role, "content": t.content} for t in self._turns]
