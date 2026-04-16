from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"

PROFILE_FILE     = DATA_DIR / "profile.json"
NOTES_FILE       = DATA_DIR / "notes.json"
TASKS_FILE       = DATA_DIR / "tasks.json"
OPERATIONS_FILE  = DATA_DIR / "operations.json"  # active tool state machine session
MEMORY_FILE      = DATA_DIR / "memory.json"       # legacy — no longer written to

# Ensure data dirs exist at import time
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
