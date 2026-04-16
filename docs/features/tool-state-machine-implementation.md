# Tool State Machine — Implementation Layer (Python)

## 🧠 Overview

This document defines how to implement the **Tool State Machine** in actual Python code.

It represents the transition from:

> “conceptual agent behavior”
> to
> **deterministic engineered system behavior**

At this stage, Astra stops relying on ad-hoc LLM decisions and becomes a **structured execution engine with persistent state control**.

---

## 🎯 Goal

To ensure that all tool execution in Astra is:

* Stateful (supports multi-step operations)
* Deterministic (no hidden assumptions)
* Recoverable (can resume incomplete operations)
* Validated (no missing required inputs at execution time)

---

## ⚙️ Core Architecture

The system introduces a dedicated **ToolStateMachine layer** between intent parsing and execution.

### Execution Flow

```text id="flow1"
User Input
   ↓
LLM Intent Parser
   ↓
ToolStateMachine
   ↓
Tool Validator
   ↓
Tool Executor
   ↓
Result Handler
```

---

## 📦 Core Data Model

Each tool operation is represented as a persistent state object.

```python id="model1"
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

@dataclass
class ToolOperationState:
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent: str = ""
    status: str = "pending"  # pending | awaiting_input | ready | executing | completed | failed
    
    required_fields: List[str] = field(default_factory=list)
    provided_fields: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)

    context: Dict = field(default_factory=dict)
```

---

## 🧠 State Machine Core Class

```python id="core1"
class ToolStateMachine:
    def __init__(self):
        self.active_operations = {}

    def create_operation(self, intent: str, required_fields: list, context: dict):
        op = ToolOperationState(
            intent=intent,
            required_fields=required_fields,
            context=context
        )
        
        self._validate_missing_fields(op)
        self.active_operations[op.operation_id] = op
        
        return op
```

---

## 🔍 Field Validation Logic

The system ensures no tool executes with incomplete data.

```python id="validate1"
    def _validate_missing_fields(self, op: ToolOperationState):
        op.missing_fields = [
            field for field in op.required_fields
            if field not in op.provided_fields
        ]

        if op.missing_fields:
            op.status = "awaiting_input"
        else:
            op.status = "ready"
```

---

## 🔁 State Update Mechanism

Used when the user continues or completes a multi-step request.

```python id="update1"
    def update_operation(self, operation_id: str, new_data: dict):
        op = self.active_operations[operation_id]

        op.provided_fields.update(new_data)
        self._validate_missing_fields(op)

        return op
```

---

## ⚙️ Execution Gate (Critical Component)

Prevents execution unless fully valid.

```python id="execute1"
    def execute_if_ready(self, op: ToolOperationState, executor_fn):
        if op.status != "ready":
            raise Exception(f"Operation not ready: missing {op.missing_fields}")

        op.status = "executing"
        result = executor_fn(op.provided_fields)
        op.status = "completed"

        return result
```

---

## 🔄 Handling Multi-Step Interactions

### Example Flow

User:

> create a markdown file called ideas.md

System:

* Creates operation
* Detects missing `content`
* Sets state → `awaiting_input`

User:

> put my name in it

System:

* Updates operation state
* Fills missing `content`
* Marks operation → `ready`
* Executes tool

---

## 🧯 Failure Handling

```python id="fail1"
    def fail_operation(self, op: ToolOperationState, error: str):
        op.status = "failed"
        op.context["error"] = error
```

---

## 📌 Key Design Principles

### 1. No Stateless Execution

Every tool call must belong to a tracked operation.

---

### 2. No Silent Defaults

Missing fields must be explicitly requested, not inferred.

---

### 3. One Operation = One Lifecycle

No duplicated execution chains for the same request.

---

### 4. State Persistence is Mandatory

Operations must survive across multiple user messages.

---

## 🚀 Why This Matters

Without a state machine:

* Astra behaves like a chat model with tools
* Multi-step workflows break easily
* Execution becomes unpredictable

With a state machine:

* Astra becomes a **deterministic agent runtime**
* Multi-turn workflows are stable
* Tool execution becomes auditable and controllable

---

## 🧭 Final Insight

This layer is the point where Astra transitions from:

> “LLM that can do things”

to:

> **an engineered system that reliably performs actions under constraints**

It is the foundational step toward scalable agent behavior.
