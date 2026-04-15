# Project Structure

This document defines the recommended modular folder structure for Astra.

The goal is to ensure:

* Clear separation of concerns
* Scalability across interfaces (CLI → Web → Mobile)
* Maintainability as the system grows

---

## 📁 Root Structure

```
astra/
├── core/
├── agents/
├── memory/
├── actions/
├── interface/
├── services/
├── utils/
├── data/
├── config/
├── tests/
├── docs/
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---

## 🧠 core/

The central orchestration layer of Astra.

### Responsibilities:

* Routing user input
* Managing system flow
* Calling agents
* Coordinating memory + actions

### Example:

```
core/
├── engine.py        # Main orchestrator
├── router.py        # Routes commands to agents
├── context.py       # Builds context for LLM
```

---

## 🤖 agents/

Specialized reasoning modules powered by LLM.

Each agent should have a **single responsibility**.

### Structure:

```
agents/
├── planner/
│   ├── agent.py
│   ├── prompt.txt
│   └── schema.py
├── reflection/
│   ├── agent.py
│   ├── prompt.txt
│   └── schema.py
├── task/
│   └── agent.py
```

### Notes:

* Keep prompts separate from logic
* Use schemas for structured outputs

---

## 🧠 memory/

Handles all persistence and retrieval.

### Structure:

```
memory/
├── store.py         # Save/load logic
├── models.py        # Data schemas
├── manager.py       # High-level memory API
├── types/
│   ├── tasks.py
│   ├── notes.py
│   └── preferences.py
```

### Responsibilities:

* Task storage
* User context
* Memory categorization

---

## ⚡ actions/

Executes real-world operations.

### Structure:

```
actions/
├── files.py         # File system operations
├── system.py        # OS-level actions
├── tasks.py         # Task manipulation
```

### Examples:

* Rename files
* Organize folders
* Update tasks

---

## 🖥️ interface/

All user interaction layers.

### Structure:

```
interface/
├── cli/
│   ├── app.py       # CLI entry point
│   ├── commands.py  # Command definitions
│   └── parser.py    # Input parsing
```

### Future:

```
interface/
├── web/
├── mobile/
```

---

## 🔌 services/

External integrations and APIs.

### Structure:

```
services/
├── llm/
│   ├── anthropic.py   # Claude API wrapper
│   └── base.py
├── scheduler.py       # Time-based triggers
```

### Responsibilities:

* API communication
* Background jobs
* Notifications (future)

---

## 🧰 utils/

Reusable helper functions.

### Examples:

```
utils/
├── logger.py
├── time.py
├── formatting.py
```

---

## 💾 data/

Local data storage (user-specific).

### Structure:

```
data/
├── tasks.json
├── memory.json
├── logs/
```

### Notes:

* Keep user data separate from logic
* Easy to migrate later (cloud sync)

---

## ⚙️ config/

Configuration and environment management.

```
config/
├── settings.py
├── constants.py
```

---

## 🧪 tests/

Testing suite.

```
tests/
├── test_core.py
├── test_memory.py
├── test_agents.py
```

---

## 🧭 main.py

Entry point for Astra.

Responsibilities:

* Initialize system
* Load configuration
* Start interface (CLI for v1)

---

## 🔁 Data Flow (Simplified)

```
User Input
   ↓
Interface (CLI)
   ↓
Core Engine
   ↓
Agent चयन (Planner / Reflection / etc.)
   ↓
Memory (read/write)
   ↓
Action Layer (if needed)
   ↓
Response → User
```

---

## 📌 Design Principles

### 1. Separation of Concerns

Each folder has a single responsibility.

### 2. Interface Independence

Core logic must not depend on CLI, Web, or Mobile.

### 3. Agent Modularity

Agents should be swappable and independent.

### 4. Memory Centralization

All state flows through the memory layer.

### 5. Scalability

Structure should support:

* More agents
* More interfaces
* More automation

---

## 🚧 Future Expansion

* Add `events/` for event-driven architecture
* Add `queue/` for async task execution
* Replace JSON with database
* Add vector memory system

---

## ✅ Summary

This structure ensures Astra remains:

* Modular
* Extensible
* Maintainable

It allows you to start simple (CLI) and scale into a full multi-platform intelligent system without rewriting the core.
