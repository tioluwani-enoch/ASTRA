# Behavioral Bugs & System Inconsistencies

## 🎯 Purpose

Document critical behavioral and architectural issues observed in Astra’s current runtime.

These issues affect:

* reliability
* consistency
* user trust
* agent correctness

---

## 🚨 1. Rename Task Failure (Critical)

### Symptom

User attempts:

> rename "Lunch with boss" → "Dinner with boss"

System response:

> No changes specified

---

### Root Cause

* Update logic fails to detect `title` as a valid change
* Field diffing mechanism is broken or incomplete
* Possible mismatch between `task_id` lookup and update payload

---

### Required Fix

* Ensure `title` is treated as a mutable field
* Fix comparison logic:

  * old value vs new value
* Always apply update when new value ≠ existing value

---

## 🚨 2. Enum Serialization Warnings (Pydantic)

### Symptom

Warnings:

```text
PydanticSerializationUnexpectedValue
```

---

### Root Cause

System passes:

```python
"low", "high"
```

Instead of:

```python
Priority.LOW, Priority.HIGH
```

---

### Required Fix

Add **Normalization Layer** before validation:

```python
def normalize_priority(value: str) -> Priority:
    return Priority[value.upper()]
```

---

## 🚨 3. Implicit Confirmation Failure

### Symptom

System asks:

> “Want me to mark this complete?”

User responds:

> “yeah”

System does:
→ nothing

---

### Root Cause

* No mapping from conversational confirmation → action execution
* No memory of pending suggestion

---

### Required Fix

Introduce:

* Confirmation intent detection
* Action binding to last suggestion

---

## 🚨 4. Missing Short-Term Conversation Memory

### Symptom

User:

> “yeah yeah”

System:

> “I don’t have context”

---

### Root Cause

* Each GENERAL_CHAT treated as stateless
* No conversational memory buffer

---

### Required Fix

Add **Conversation Memory Layer**

Example:

```json
{
  "last_action": "mark_task_complete",
  "target_task_id": "f708a8f6"
}
```

---

## 🚨 5. Suggestion → Action Gap

### Symptom

System suggests an action but cannot follow through when user agrees.

---

### Root Cause

* Suggestions are not stored as executable intents
* No linkage between suggestion and tool execution

---

### Required Fix

* Store suggestions as structured actions
* Allow user confirmation to trigger execution

---

## 🧭 Priority Order

1. Fix UPDATE_TASK logic (rename bug)
2. Add enum normalization
3. Add confirmation resolver
4. Add conversation memory layer
5. Link suggestions → executable actions

---

## 🚀 Expected Outcome

* Task updates behave correctly
* No runtime warnings
* Conversations feel continuous
* Agent executes implied user intent
* Astra behaves more like a real assistant
