# Astra — Personal AI Chief of Staff

Astra is a hybrid AI assistant designed to function as both a **thinking partner** and a **task execution system**.
It is built to help manage daily decisions, tasks, and workflows through memory, planning, and controlled autonomy.

> Astra is not just a chatbot. It is a system that evolves with you.

---

## ✨ Core Philosophy

Astra operates as a **Personal Chief of Staff + Cognitive Amplifier**:

* Plans your day intelligently
* Tracks and prioritizes tasks
* Learns your habits over time
* Executes structured, repeatable actions
* Intervenes only when necessary

---

## 🧠 Key Capabilities (v1 Focus)

* **Daily Planning Engine**

  * Generate realistic schedules based on tasks and constraints

* **Task Intelligence**

  * Priority-aware task management
  * Time estimation and dependency handling

* **Memory System**

  * Persistent user context (projects, preferences, habits)

* **Reflection Loop**

  * End-of-day review to improve future planning

* **CLI Interface**

  * Fast, minimal interface for interacting with Astra

---

## 🏗️ Architecture Overview

Astra is designed as a **backend-first system** with modular interfaces.

```
astra/
├── core/          # Core logic (planning, reasoning, orchestration)
├── memory/        # Memory storage + retrieval
├── agents/        # Task-specific logic (planner, executor, etc.)
├── actions/       # System actions (file ops, automation)
├── interface/
│   └── cli/       # Command-line interface (v1)
├── data/          # Local user data (tasks, logs, memory)
├── docs/          # Project documentation
└── README.md
```

---

## ⚙️ Tech Stack

* **Language:** Python
* **LLM Provider:** Anthropic (Claude API)
* **Storage (v1):** JSON / SQLite
* **Interface (v1):** CLI

---

## 🚀 Getting Started

### 1. Clone the repository

```
git clone https://github.com/yourusername/astra.git
cd astra
```

### 2. Set up environment

```
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
```

### 4. Run Astra (CLI)

```
python main.py
```

---

## 💬 Example Usage

```
> plan my day
> add task "Finish ML pipeline"
> what should I do next?
> reflect on today
```

---

## 🧩 Roadmap

### v1 (Current)

* CLI interface
* Task + planning system
* Basic memory

### v2

* Proactive assistant behavior
* Improved memory (semantic retrieval)
* File system automation

### v3

* Web dashboard
* Cross-device sync

### v4

* Mobile integration
* Voice interface

---

## ⚠️ Design Principles

* Start simple, iterate fast
* Memory > UI
* Usefulness over features
* Controlled proactivity (no noise)

---

## 📌 Status

🚧 In active development — focused on building a robust core system before expanding interfaces.

---

## 🤝 Contributing

This is currently a personal project, but contributions and ideas are welcome in the future.

---

## 📜 License

MIT License
