# Intent Collapse: File vs Note Misclassification

## 🚨 Problem Summary

The system incorrectly maps **file creation requests** to **note storage actions**, resulting in loss of structure, metadata, and user intent fidelity.

This occurs when the assistant collapses distinct concepts:

* Files (filesystem objects)
* Notes (memory objects)
* Documents (structured text artifacts)

into a single generalized storage action.

---

## ⚠️ Observed Failure Pattern

### User Intent Example:

> "create an idea markdown file with my name init"

### Incorrect System Output:

```json
{
  "intent": "ADD_NOTE",
  "content": "# Ideas\n\nAuthor: <UNKNOWN>"
}
```

### Expected Output:

```json
{
  "intent": "CREATE_FILE",
  "parameters": {
    "filename": "ideas.md",
    "content": "# Ideas\n\nAuthor: Tioluwani"
  }
}
```

---

## ❌ Core Issues

### 1. Intent Misclassification

File-related requests are incorrectly mapped to:

* `ADD_NOTE`

Instead of:

* `CREATE_FILE`

---

### 2. Loss of Entity Information

User-provided metadata is dropped:

* Name (author)
* Filename inference
* File type (markdown)

---

### 3. Concept Overloading

The system treats all of the following as identical:

* notes
* markdown files
* documents
* ideas

This results in structural ambiguity.

---

## 🧠 Root Cause

The LLM is performing **semantic compression**:

> “markdown file” → “note”

This is a natural language shortcut, but it is **architecturally invalid** in a structured agent system.

Current pipeline:

```
LLM → Generic Intent (ADD_NOTE) → Memory Storage
```

Missing:

```
LLM → Structured Intent (CREATE_FILE) → Tool Router → Filesystem Execution
```

---

## 🧱 Required Fix: Primitive Separation

The system must explicitly distinguish:

### 📄 File

* Exists in filesystem
* Has filename and path
* Supports structured content (e.g., markdown)

### 🧠 Note

* Exists in memory store
* No filesystem representation
* Lightweight contextual storage

### 📋 Task

* Action-oriented entity
* Time / priority based
* Requires lifecycle tracking

---

## ⚙️ Required Intent Schema Update

### Must include explicit intent types:

```json
{
  "intent": "CREATE_FILE | ADD_NOTE | ADD_TASK"
}
```

### File-specific structure:

```json
{
  "intent": "CREATE_FILE",
  "parameters": {
    "filename": "ideas.md",
    "content": "...",
    "author": "..."
  }
}
```

---

## 🚫 Forbidden Behavior

* Converting file requests into notes silently
* Dropping filename or author metadata
* Merging storage systems without explicit mapping
* Guessing storage type without structured validation

---

## 🧯 Required System Rules

### Rule 1 — Explicit File Detection

If input contains any of:

* “file”
* “markdown”
* “.md / .txt / .json”
* “save as”

→ MUST classify as `CREATE_FILE`

---

### Rule 2 — No Implicit Substitution

The system must not silently downgrade:

* CREATE_FILE → ADD_NOTE

Any mismatch must be explicitly logged or corrected.

---

### Rule 3 — Preserve User Entities

All user-provided metadata must be preserved:

* names
* filenames
* formats

---

## 🔧 Recommended Fix Strategy

### Step 1: Expand Intent Types

Introduce:

* CREATE_FILE
* READ_FILE
* UPDATE_FILE
* ADD_NOTE
* ADD_TASK

---

### Step 2: Add Pre-Parsing Entity Extraction

Extract before classification:

* filename
* file type
* author reference

---

### Step 3: Implement Deterministic Tool Router

Map intents directly:

```
CREATE_FILE → filesystem.create()
ADD_NOTE → memory.store()
```

No overlap allowed.

---

### Step 4: Add Debug Logging

Log:

* raw user input
* extracted entities
* chosen intent
* execution target

---

## 📌 Key Insight

The system failure is not linguistic—it is **structural**:

> The model is allowed to blur distinctions that the system must enforce.

---

## 🚀 Expected Outcome After Fix

* Correct separation of files vs notes
* Preservation of user metadata
* Predictable tool execution
* Improved reliability for agent workflows

---

## 🧭 Priority Level

**HIGH** — must be resolved before:

* expanding memory system
* adding web interface
* introducing autonomous behavior
