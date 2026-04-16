# 🧩 Astra — Structured Response Schema

## Goal

Move from plain text responses to **structured JSON outputs** so the frontend can render intelligently.

---

## 🧠 Why This Matters

Current system:
- Returns raw text
- Hard to parse in UI

New system:
- Returns typed JSON
- UI can render components (tasks, confirmations, etc.)

---

## 📦 Base Response Schema

```json
{
  "type": "string",
  "message": "string",
  "data": {}
}
```

---

## 🔹 Response Types

### 1. Chat

```json
{
  "type": "chat",
  "message": "Hey Enoch! What's up?",
  "data": {}
}
```

---

### 2. Task List

```json
{
  "type": "task_list",
  "message": "Here are your tasks",
  "data": {
    "tasks": [
      {
        "id": "abc123",
        "title": "Dinner with boss",
        "priority": "HIGH",
        "due_date": "2026-04-16",
        "status": "TODO"
      }
    ]
  }
}
```

---

### 3. Task Created

```json
{
  "type": "task_created",
  "message": "Task added successfully",
  "data": {
    "task": {
      "id": "xyz789",
      "title": "Hackathon",
      "priority": "MEDIUM"
    }
  }
}
```

---

### 4. Task Updated

```json
{
  "type": "task_updated",
  "message": "Task updated",
  "data": {
    "task_id": "abc123",
    "changes": {
      "title": "Dinner with boss",
      "priority": "HIGH"
    }
  }
}
```

---

### 5. Confirmation Required

```json
{
  "type": "confirmation",
  "message": "Mark task as complete?",
  "data": {
    "action": "mark_complete",
    "task_id": "abc123"
  }
}
```

---

### 6. Error

```json
{
  "type": "error",
  "message": "Task not found",
  "data": {}
}
```

---

## 🔌 Backend Integration

### Modify Engine Output

Instead of:

```python
return "Task added"
```

Return:

```python
return {
  "type": "task_created",
  "message": "Task added",
  "data": {...}
}
```

---

## 🧱 Helper Builder (Recommended)

```python
def build_response(type, message, data=None):
    return {
        "type": type,
        "message": message,
        "data": data or {}
    }
```

---

## 🎯 Frontend Mapping

| type            | UI Component        |
|-----------------|--------------------|
| chat            | text bubble        |
| task_list       | task list UI       |
| task_created    | toast / card       |
| task_updated    | update animation   |
| confirmation    | buttons (yes/no)   |
| error           | error banner       |

---

## ✅ Migration Strategy

1. Keep existing text responses working
2. Gradually replace with structured responses
3. Update frontend to use `type`

---

## 🧠 Principle

Backend decides **what happened**  
Frontend decides **how it looks**
