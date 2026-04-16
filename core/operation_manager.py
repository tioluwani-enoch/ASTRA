"""
OperationManager — high-level wrapper over ToolStateMachine.

Concerns:
  - Persistence (data/operations.json) — survives process restarts
  - LLM continuation — extract missing fields from follow-up messages
  - Natural-language prompts — tell the user what's missing
  - IntentResult → ToolStateMachine bridge

Does NOT own state transitions. Those belong to ToolStateMachine.
"""
from __future__ import annotations

import json
from typing import Any, Callable, TYPE_CHECKING

from config.constants import OPERATIONS_FILE
from core.operation import Operation, OperationStatus
from core.state_machine import ToolStateMachine
from core.tool_schemas import TOOL_SCHEMAS
from utils.logger import get_logger

if TYPE_CHECKING:
    from core.intent import IntentResult
    from services.llm.anthropic import AnthropicService

logger = get_logger(__name__)

_FIELD_PROMPTS: dict[str, str] = {
    "filename": "What should the file be called?",
    "content":  "What content should go in it?",
    "author":   "Who is the author?",
    "title":    "What's the task title?",
    "key":      "Which field do you want to update?",
    "value":    "What should it be set to?",
    "message":  "What's your message?",
}


class OperationManager:
    def __init__(self) -> None:
        self._tsm = ToolStateMachine()
        self._restore_from_disk()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _restore_from_disk(self) -> None:
        if not OPERATIONS_FILE.exists():
            return
        try:
            data = json.loads(OPERATIONS_FILE.read_text(encoding="utf-8"))
            op = Operation.model_validate(data)
            if op.status == OperationStatus.AWAITING_INPUT:
                self._tsm.restore([op])
        except Exception as exc:
            logger.warning(f"[OP_MANAGER] Could not restore state: {exc}")

    def _save(self) -> None:
        pending = self._tsm.get_pending()
        if pending:
            OPERATIONS_FILE.write_text(pending.model_dump_json(indent=2), encoding="utf-8")
        else:
            OPERATIONS_FILE.unlink(missing_ok=True)

    # ── State queries ─────────────────────────────────────────────────────────

    def has_pending(self) -> bool:
        return self._tsm.get_pending() is not None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def create_from_action(self, pending_action) -> Operation:
        """
        Build an Operation directly from a PendingAction (confirmed suggestion).
        Bypasses the LLM intent parser — the action is already structured.
        """
        intent = pending_action.action
        params: dict = {}
        if pending_action.target_id:
            params["task_id"] = pending_action.target_id
        params.update(pending_action.payload or {})

        schema = TOOL_SCHEMAS.get(intent, {"required": [], "optional": []})
        op = self._tsm.create_operation(
            intent=intent,
            required_fields=schema["required"],
            provided_fields=params,
            context={"original_request": f"confirmed: {intent}"},
        )
        self._save()
        logger.info(f"[OP_MANAGER] Created from action {op}")
        return op

    def create(self, intent_result: IntentResult, user_input: str) -> Operation:
        """Translate an IntentResult into an Operation and register it in the TSM."""
        schema = TOOL_SCHEMAS.get(intent_result.intent.value, {"required": [], "optional": []})
        op = self._tsm.create_operation(
            intent=intent_result.intent.value,
            required_fields=schema["required"],
            provided_fields=dict(intent_result.parameters),
            context={"original_request": user_input},
        )
        self._save()
        logger.info(f"[OP_MANAGER] Created {op}")
        return op

    def try_continue(self, user_input: str, llm: AnthropicService) -> Operation:
        """
        A follow-up message arrived for a pending AWAITING_INPUT operation.
        Use the LLM to extract the missing fields, then update via TSM.
        """
        pending = self._tsm.get_pending()
        assert pending is not None

        filled = llm.extract_fields(
            user_input,
            pending.missing_fields,
            {"intent": pending.intent, "original_request": pending.context.get("original_request", "")},
        )
        if filled:
            op = self._tsm.update_operation(pending.operation_id, filled)
            self._save()
            logger.info(f"[OP_MANAGER] Continued {op.operation_id} | filled={list(filled.keys())} | status={op.status}")
            return op

        logger.debug("[OP_MANAGER] No new fields extracted from follow-up")
        return pending

    def execute_if_ready(
        self,
        op: Operation,
        executor_fn: Callable[[dict[str, Any]], str],
    ) -> str:
        """Delegate to TSM gate, then persist the cleared state."""
        result = self._tsm.execute_if_ready(op, executor_fn)
        self._save()
        return result

    def fail_active(self, error: str) -> None:
        pending = self._tsm.get_pending()
        if pending:
            self._tsm.fail_operation(pending, error)
            self._save()

    def prompt_for_missing(self) -> str:
        pending = self._tsm.get_pending()
        assert pending is not None
        prompts = [
            _FIELD_PROMPTS.get(f, f"What is the {f.replace('_', ' ')}?")
            for f in pending.missing_fields
        ]
        intent_label = pending.intent.replace("_", " ")
        if len(prompts) == 1:
            return f"To {intent_label}, I need one more thing — {prompts[0]}"
        fields_str = "\n".join(f"  • {p}" for p in prompts)
        return f"To {intent_label}, I still need:\n{fields_str}"
