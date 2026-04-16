from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class OperationStatus(str, Enum):
    INITIATED     = "initiated"
    AWAITING_INPUT = "awaiting_input"
    READY         = "ready"
    EXECUTING     = "executing"
    COMPLETED     = "completed"
    FAILED        = "failed"


class Operation(BaseModel):
    operation_id:    str                  = Field(default_factory=lambda: str(uuid4())[:8])
    intent:          str
    status:          OperationStatus      = OperationStatus.INITIATED
    required_fields: list[str]            = Field(default_factory=list)
    provided_fields: dict[str, Any]       = Field(default_factory=dict)
    missing_fields:  list[str]            = Field(default_factory=list)
    context:         dict[str, Any]       = Field(default_factory=dict)
    created_at:      str                  = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at:      str                  = Field(default_factory=lambda: datetime.now().isoformat())

    def validate_fields(self) -> None:
        """Compute missing_fields and transition to READY or AWAITING_INPUT."""
        self.missing_fields = [
            f for f in self.required_fields
            if not self.provided_fields.get(f)
        ]
        self.status = (
            OperationStatus.AWAITING_INPUT
            if self.missing_fields
            else OperationStatus.READY
        )
        self.updated_at = datetime.now().isoformat()

    def merge_params(self, params: dict[str, Any]) -> None:
        """Merge newly provided params and re-validate."""
        self.provided_fields.update({k: v for k, v in params.items() if v})
        self.validate_fields()

    def mark_executing(self) -> None:
        self.status = OperationStatus.EXECUTING
        self.updated_at = datetime.now().isoformat()

    def mark_completed(self) -> None:
        self.status = OperationStatus.COMPLETED
        self.updated_at = datetime.now().isoformat()

    def mark_failed(self, error: str) -> None:
        self.status = OperationStatus.FAILED
        self.context["error"] = error
        self.updated_at = datetime.now().isoformat()

    def __str__(self) -> str:
        return (
            f"Operation(id={self.operation_id}, intent={self.intent}, "
            f"status={self.status}, missing={self.missing_fields})"
        )
