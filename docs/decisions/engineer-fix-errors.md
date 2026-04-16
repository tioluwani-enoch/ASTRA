# Astra Engineering Task: Fix Current System Errors

## 🎯 Objective

Stabilize the current Astra agent system by fixing structural inconsistencies in:

* task duplication
* temporal parsing
* entity resolution gaps
* intent ambiguity between create vs update operations

This is a **stability patch**, not a feature expansion.

---

## 🚨 Critical Issues to Fix

### 1. Task Duplication Problem

#### Symptom

Same logical task is created multiple times:

* identical title
* identical context
* no deduplication

#### Required Fix

Implement **Task Identity Resolver**:

* Compare new task intent against existing tasks
* Match on:

  * title similarity
  * temporal proximity
  * semantic similarity (optional embedding or heuristic)
* If match found:

  * update existing task instead of creating new one

#### Expected Behavior

* “Lunch with boss at 7 PM” → single task only
* follow-up messages → update task, not duplicate

---

### 2. Missing Temporal Normalization

#### Symptom

Inputs like:

* “7 PM”
* “tomorrow”
* “next Friday”

are stored as:

* `<UNKNOWN>` or raw strings

#### Required Fix

Add **Temporal Parsing Layer**

Convert natural language → ISO 8601 datetime.

Example:

* “7 PM today” → `2026-04-15T19:00:00`

Rules:

* Always normalize time-based fields before task creation
* Never store raw time strings in task objects

---

### 3. Intent Ambiguity: CREATE vs UPDATE

#### Symptom

System always triggers:

* CREATE_TASK even when updating is intended

#### Required Fix

Add **Intent Disambiguation Layer**

Before execution:

Determine:

* Is this a new entity?
* Or modification of existing entity?

Heuristics:

* If similar task exists → UPDATE_TASK
* If no match → CREATE_TASK

---

### 4. Lack of Entity Linking

#### Symptom

Multiple tasks represent the same real-world object

#### Required Fix

Introduce:

* `entity_id` for tasks
* canonical task representation
* alias references from follow-up messages

---

## 🧱 Required Architecture Change

Add this pre-execution layer:

```text
User Input
  ↓
Intent Parser
  ↓
Entity Resolver (NEW)
  ↓
Temporal Parser (NEW)
  ↓
Task State Machine
  ↓
Execution Layer
```

---

## 🧯 Constraints

* Do NOT break existing tool interfaces
* Do NOT remove state machine
* Maintain backward compatibility with current intents

---

## 📌 Success Criteria

* No duplicate tasks from repeated user references
* All time inputs normalized
* Updates correctly modify existing tasks
* Entity identity is consistent across sessions

---

## 🚀 Outcome

After fix:

* Task system becomes deterministic
* No duplicate or fragmented entries
* Time-aware scheduling becomes reliable
