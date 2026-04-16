"""
ToolStateMachine — deterministic execution control layer.

Implements the state machine described in features/tool-state-machine-implementation.md.

Responsibilities:
  - Track active operations as stateful objects (keyed by operation_id)
  - Validate required fields on create and update
  - Gate execution: execute_if_ready() raises if fields are missing
  - Transition states: INITIATED → AWAITING_INPUT/READY → EXECUTING → COMPLETED/FAILED

This class has NO knowledge of persistence, LLM, or prompts.
Those concerns belong to OperationManager, which wraps this class.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from core.operation import Operation, OperationStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class ToolStateMachine:
    def __init__(self) -> None:
        # All active operations, keyed by operation_id.
        # One AWAITING_INPUT op at a time in practice; dict allows future parallel tracking.
        self.active_operations: dict[str, Operation] = {}

    # ── Create ────────────────────────────────────────────────────────────────

    def create_operation(
        self,
        intent: str,
        required_fields: list[str],
        provided_fields: dict[str, Any],
        context: dict[str, Any],
    ) -> Operation:
        op = Operation(
            intent=intent,
            required_fields=required_fields,
            provided_fields=provided_fields,
            context=context,
        )
        self._validate_missing_fields(op)
        self.active_operations[op.operation_id] = op
        logger.debug(f"[TSM] Created {op}")
        return op

    # ── Validate ──────────────────────────────────────────────────────────────

    def _validate_missing_fields(self, op: Operation) -> None:
        """Compute missing_fields and transition to READY or AWAITING_INPUT."""
        op.missing_fields = [
            f for f in op.required_fields
            if not op.provided_fields.get(f)
        ]
        op.status = (
            OperationStatus.AWAITING_INPUT
            if op.missing_fields
            else OperationStatus.READY
        )
        op.updated_at = datetime.now().isoformat()

    # ── Update ────────────────────────────────────────────────────────────────

    def update_operation(self, operation_id: str, new_data: dict[str, Any]) -> Operation:
        """Merge new field data into an existing operation and re-validate."""
        op = self.active_operations[operation_id]
        op.provided_fields.update({k: v for k, v in new_data.items() if v})
        self._validate_missing_fields(op)
        logger.debug(f"[TSM] Updated {op.operation_id} | status={op.status} | missing={op.missing_fields}")
        return op

    # ── Execute ───────────────────────────────────────────────────────────────

    def execute_if_ready(
        self,
        op: Operation,
        executor_fn: Callable[[dict[str, Any]], str],
    ) -> str:
        """
        Gate: raises ValueError if op is not READY.
        Transitions READY → EXECUTING → COMPLETED (or removes on exception).
        Returns the result string from executor_fn.
        """
        if op.status != OperationStatus.READY:
            raise ValueError(
                f"Operation {op.operation_id} cannot execute: "
                f"status={op.status}, missing={op.missing_fields}"
            )

        op.mark_executing()
        logger.info(f"[TSM] Executing {op.operation_id} | {op.intent}")

        try:
            result = executor_fn(op.provided_fields)
        except Exception as exc:
            self.active_operations.pop(op.operation_id, None)
            raise exc

        op.mark_completed()
        self.active_operations.pop(op.operation_id, None)
        logger.info(f"[TSM] Completed {op.operation_id}")
        return result

    # ── Fail ──────────────────────────────────────────────────────────────────

    def fail_operation(self, op: Operation, error: str) -> None:
        op.mark_failed(error)
        self.active_operations.pop(op.operation_id, None)
        logger.error(f"[TSM] Failed {op.operation_id}: {error}")

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_pending(self) -> Operation | None:
        """Return the first AWAITING_INPUT operation, if any."""
        for op in self.active_operations.values():
            if op.status == OperationStatus.AWAITING_INPUT:
                return op
        return None

    # ── Restore ───────────────────────────────────────────────────────────────

    def restore(self, ops: list[Operation]) -> None:
        """Load previously persisted operations back into the active dict."""
        for op in ops:
            self.active_operations[op.operation_id] = op
            logger.info(f"[TSM] Restored {op}")
