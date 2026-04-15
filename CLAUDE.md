# Astra — CLAUDE.md

Astra is a personal AI assistant (Personal Chief of Staff) built in Python using the Anthropic Claude API.
It is **currently in early development** — only documentation exists, no code yet.

## Goal

Build a persistent, intelligent system that:
- Plans the user's day
- Tracks and prioritizes tasks
- Learns habits and preferences over time
- Executes structured, repeatable actions via CLI (v1)

## Tech Stack

- **Language:** Python
- **LLM:** Anthropic Claude API (use `claude-sonnet-4-6` or `claude-opus-4-6`)
- **Storage (v1):** JSON files in `data/`, with SQLite as a future upgrade
- **Interface (v1):** CLI only

## Project Structure

```
astra/
├── core/
│   ├── engine.py        # Main orchestrator — routes input, manages flow
│   ├── router.py        # Routes commands to the right agent
│   └── context.py       # Builds LLM context from memory + session
├── agents/
│   ├── planner/         # Breaks goals into schedules (agent.py, prompt.txt, schema.py)
│   ├── reflection/      # End-of-day review (agent.py, prompt.txt, schema.py)
│   └── task/            # Task CRUD logic
├── memory/
│   ├── manager.py       # High-level memory API
│   ├── store.py         # Save/load to disk
│   ├── models.py        # Data schemas (Pydantic)
│   └── types/           # tasks.py, notes.py, preferences.py
├── actions/
│   ├── files.py         # File system operations
│   ├── system.py        # OS-level actions
│   └── tasks.py         # Task manipulation helpers
├── interface/
│   └── cli/
│       ├── app.py       # CLI entry point (Typer or argparse)
│       ├── commands.py  # Command definitions
│       └── parser.py    # Input parsing
├── services/
│   └── llm/
│       ├── base.py      # Abstract LLM interface
│       └── anthropic.py # Claude API wrapper
├── utils/
│   ├── logger.py
│   ├── time.py
│   └── formatting.py
├── config/
│   ├── settings.py      # Load .env, build config object
│   └── constants.py
├── data/                # Runtime user data (gitignored)
│   ├── tasks.json
│   ├── memory.json
│   └── logs/
├── tests/
├── main.py              # Entry point: init config, start CLI
├── requirements.txt
└── .env                 # ANTHROPIC_API_KEY (never commit)
```

## Data Flow

```
User Input → CLI → Core Engine → Agent (Planner/Reflection/Task)
                                      ↕ Memory (read/write)
                                      ↓ Action Layer (if needed)
                               Response → User
```

## Core Loop

1. **Plan** — Generate daily structure from tasks + context
2. **Act** — Execute and track tasks
3. **Reflect** — End-of-day review, improve future planning

## v1 CLI Commands

- `plan` — generate a daily schedule
- `task add/remove/list` — task management
- `reflect` — end-of-day review
- `note` — save a quick note

## Design Principles (non-negotiable)

1. **Usefulness first** — every feature must provide real daily value
2. **Memory over interface** — smart core beats polished UI
3. **Controlled proactivity** — assist, don't interrupt
4. **Human-in-the-loop** — user always has final control
5. **Interface independence** — core logic must not depend on CLI/Web/Mobile
6. **Agent modularity** — agents must be focused, single-responsibility, swappable

## Claude API Usage Notes

- Always use prompt caching where possible (large system prompts, memory context)
- Structured outputs via tool use / JSON schemas for agent responses
- Keep LLM calls in `services/llm/anthropic.py`, never scattered across modules
- Use `claude-sonnet-4-6` as the default model for cost/performance balance
