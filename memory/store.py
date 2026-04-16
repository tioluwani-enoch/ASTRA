"""
Store layer — one load/save pair per memory type.
Each store writes to its own file so reads are always targeted, not a full scan.

  profile.json  → UserProfile
  notes.json    → list[Note]
  tasks.json    → TaskStore (tasks + preferences)
"""
import json

from config.constants import PROFILE_FILE, NOTES_FILE, TASKS_FILE
from .models import UserProfile, Note, TaskStore


# ── Profile ───────────────────────────────────────────────────────────────────

def load_profile() -> UserProfile:
    if PROFILE_FILE.exists():
        return UserProfile.model_validate(
            json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        )
    return UserProfile()


def save_profile(profile: UserProfile) -> None:
    PROFILE_FILE.write_text(profile.model_dump_json(indent=2), encoding="utf-8")


# ── Notes ─────────────────────────────────────────────────────────────────────

def load_notes() -> list[Note]:
    if NOTES_FILE.exists():
        data = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        return [Note.model_validate(n) for n in data]
    return []


def save_notes(notes: list[Note]) -> None:
    NOTES_FILE.write_text(
        json.dumps([n.model_dump() for n in notes], indent=2),
        encoding="utf-8",
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────

def load_tasks() -> TaskStore:
    if TASKS_FILE.exists():
        return TaskStore.model_validate(
            json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        )
    return TaskStore()


def save_tasks(store: TaskStore) -> None:
    TASKS_FILE.write_text(store.model_dump_json(indent=2), encoding="utf-8")
