# Architecture

Astra follows a **modular, backend-first architecture**.

---

## Core Components

### 1. Core Engine

Responsible for:

* Orchestration
* Decision-making
* Communication with LLM

---

### 2. Memory System

Stores:

* Tasks
* User preferences
* Context

Types:

* Short-term
* Long-term
* Structured

---

### 3. Agents

Specialized modules:

* Planner Agent
* Reflection Agent
* (Future) Execution Agent

---

### 4. Action Layer

Handles real-world operations:

* File system actions
* Automation scripts
* External integrations

---

### 5. Interface Layer

Current:

* CLI

Future:

* Web app
* Mobile

---

## Design Principle

All interfaces communicate with the same core system.
