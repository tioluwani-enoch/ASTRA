# Tool State Machine Design (Critical Architecture Layer)

## 🚨 Problem Summary

The current Astra system executes tools in a **stateless, single-step pipeline**:

```
LLM → Intent → Tool Execution → Response
```

This breaks down when:

* Tool inputs are incomplete
* Multi-step actions are required
* User provides incremental instructions
* System needs clarification before execution

As a result, tool execution becomes:

* inconsistent
* conversationally fragile
* prone to partial or incorrect actions

---

## ⚠️ Observed Failure Patterns

### 1. Multi-step tool fragmentation

Example flow:

User:

> create a markdown file called ideas.md with my name

System:

* executes CREATE_FILE without full content
* later asks for missing information

Then user:

> put my name in it

System:

* starts a new CREATE_FILE instead of continuing previous context

### Issue:

No continuity across tool execution steps.

---

### 2. Missing execution memory

Each user message is treated independently:

* no awareness of pending operations
* no tool session tracking
* no state persistence between steps

---

### 3. Implicit tool completion

The system attempts to “guess” missing parameters:

* infers content
* assumes defaults
* silently substitutes values

This leads to unpredictable behavior.

---

## 🧠 Root Cause

Lack of a **Tool State Machine layer** between intent parsing and execution.

Current architecture:

```
LLM → Intent → Tool Execution (stateless)
```

Required architecture:

```
LLM → Intent → State Machine → Tool Execution → Completion
```

---

## 🧱 Required Solution: Tool State Machine

The system must explicitly track tool execution states.

---

## ⚙️ Core Concept

Each tool execution is treated as a **stateful session**, not a one-off call.

---

## 📦 Tool State Model

Each active operation must have:

```json id="state1"
{
  "operation_id": "uuid",
  "intent": "CREATE_FILE",
  "status": "pending | awaiting_input | executing | completed | failed",
  "required_fields": ["filename", "content"],
  "provided_fields": {
    "filename": "ideas.md"
  },
  "missing_fields": ["content"],
  "context": {
    "original_request": "create markdown file called ideas.md with my name"
  }
}
```

---

## 🔁 State Lifecycle

### 1. INITIATED

* Intent is recognized
* Tool session is created

---

### 2. VALIDATION

* Required fields checked
* Missing fields identified

---

### 3. AWAITING INPUT

* System requests missing information
* State is persisted

---

### 4. READY

* All required data present
* Execution permitted

---

### 5. EXECUTING

* Tool is actively running

---

### 6. COMPLETED

* Result stored
* State archived or deleted

---

### 7. FAILED

* Execution error recorded
* State preserved for debugging

---

## 🧠 Key Behavioral Rules

### Rule 1 — No execution without full state

A tool MUST NOT execute unless:

* all required fields are satisfied
* state == READY

---

### Rule 2 — Preserve operation continuity

If a tool is pending:

* new user messages MUST be checked against active state
* continuation is preferred over restarting

---

### Rule 3 — One operation per intent session

Do not spawn duplicate tool executions for the same logical request.

---

### Rule 4 — Explicit missing field handling

If data is missing:

* system must ask for it explicitly
* must NOT infer silently

---

## 🔄 State Machine Flow

```
User Input
   ↓
Intent Parser
   ↓
State Machine Check
   ↓
[No Active State]
   → Create New Operation
   ↓
[Active State Exists]
   → Update State
   ↓
Validate Fields
   ↓
If Missing → Request Input
If Ready → Execute Tool
   ↓
Store Result
```

---

## ⚙️ Tool Registry Integration

Each tool defines:

```json id="tool1"
{
  "name": "CREATE_FILE",
  "required_fields": ["filename", "content"],
  "optional_fields": ["author"],
  "execution_mode": "filesystem.write"
}
```

State machine enforces this schema strictly.

---

## 🚫 Forbidden Behaviors

* Executing tools with missing required fields
* Restarting tool flow on follow-up messages
* Inferring missing structured parameters without state tracking
* Treating multi-turn tool execution as independent calls

---

## 🧯 Required System Additions

### 1. Operation Manager

Responsible for:

* tracking active tool sessions
* updating state
* resolving completion conditions

---

### 2. State Store

Persistent storage of:

* active operations
* completed operations (optional logging)

---

### 3. State Resolver

Matches incoming user input to:

* existing operation continuation
* or new operation creation

---

## 📌 Key Insight

The system failure is not in intent detection—it is in:

> **lack of execution continuity across multiple interactions**

---

## 🚀 Expected Outcome After Implementation

* Multi-step tasks become reliable
* No duplicated or fragmented tool executions
* Clear handling of missing parameters
* Predictable agent behavior
* Foundation for autonomous workflows

---

## 🧭 Priority Level

**CRITICAL** — must be implemented before:

* advanced planning agents
* proactive automation
* multi-tool chaining
* mobile/web expansion
