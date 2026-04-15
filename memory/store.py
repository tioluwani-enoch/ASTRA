import json
from pathlib import Path

from config.constants import TASKS_FILE, MEMORY_FILE
from .models import MemoryStore


def load() -> MemoryStore:
    if MEMORY_FILE.exists():
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return MemoryStore.model_validate(data)
    return MemoryStore()


def save(store: MemoryStore) -> None:
    MEMORY_FILE.write_text(
        store.model_dump_json(indent=2),
        encoding="utf-8",
    )
