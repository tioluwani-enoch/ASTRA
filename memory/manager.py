"""
MemoryManager — high-level API over three stratified stores.

Retrieval priority (from memory-overload-and-identity-design.md):
  1. USER_PROFILE  — deterministic, schema-validated, queried directly
  2. TASKS         — action-oriented, lifecycle-tracked
  3. NOTES         — unstructured, ephemeral
  4. LLM inference — only if no structured data exists (handled in context_snapshot)

Identity data MUST go through the profile store.
Notes MUST NOT contain identity or task data.
"""
from .models import UserProfile, Note, Task, TaskStore, Preferences, TaskStatus, Priority
from . import store as _store


class MemoryManager:
    def __init__(self):
        self._profile: UserProfile = _store.load_profile()
        self._notes: list[Note]   = _store.load_notes()
        self._tasks: TaskStore    = _store.load_tasks()

    # ── Profile ───────────────────────────────────────────────────────────────
    # Deterministic access only — never inferred by LLM.

    def get_profile(self) -> UserProfile:
        return self._profile

    def get_profile_field(self, key: str) -> str | None:
        """Direct field lookup — no LLM involvement."""
        return self._profile.get_field(key)

    def update_profile(self, key: str, value: str) -> None:
        self._profile.set_field(key, value)
        _store.save_profile(self._profile)

    # ── Notes ─────────────────────────────────────────────────────────────────

    def add_note(self, content: str) -> Note:
        note = Note(content=content)
        self._notes.append(note)
        _store.save_notes(self._notes)
        return note

    def get_notes(self) -> list[Note]:
        return list(self._notes)

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        due_date: str | None = None,
    ) -> Task:
        task = Task(title=title, description=description, priority=priority, due_date=due_date)
        self._tasks.tasks.append(task)
        _store.save_tasks(self._tasks)
        return task

    def get_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        if status is None:
            return list(self._tasks.tasks)
        return [t for t in self._tasks.tasks if t.status == status]

    def update_task(self, task_id: str, **kwargs) -> Task | None:
        """Partially update a task's fields. Returns the updated task or None if not found."""
        for task in self._tasks.tasks:
            if task.id == task_id:
                task.update_fields(**kwargs)
                _store.save_tasks(self._tasks)
                return task
        return None

    def complete_task(self, task_id: str) -> Task | None:
        for task in self._tasks.tasks:
            if task.id == task_id:
                task.complete()
                _store.save_tasks(self._tasks)
                return task
        return None

    def remove_task(self, task_id: str) -> bool:
        before = len(self._tasks.tasks)
        self._tasks.tasks = [t for t in self._tasks.tasks if t.id != task_id]
        if len(self._tasks.tasks) < before:
            _store.save_tasks(self._tasks)
            return True
        return False

    # ── Preferences ───────────────────────────────────────────────────────────

    def get_preferences(self) -> Preferences:
        return self._tasks.preferences

    def update_preference(self, key: str, value: str) -> None:
        prefs = self._tasks.preferences
        if hasattr(prefs, key):
            setattr(prefs, key, value)
        else:
            prefs.extras[key] = value
        _store.save_tasks(self._tasks)

    # ── LLM context snapshot ──────────────────────────────────────────────────
    # Retrieval priority: profile first, tasks second, notes last.

    def context_snapshot(self) -> dict:
        pending = self.get_tasks(TaskStatus.TODO)
        in_progress = self.get_tasks(TaskStatus.IN_PROGRESS)

        profile_data = {}
        if not self._profile.is_empty():
            profile_data = {
                k: v for k, v in self._profile.model_dump().items()
                if k != "updated_at" and v
            }

        return {
            # 1. Identity — highest priority, always first
            "user_profile": profile_data,
            # 2. Tasks
            "pending_tasks": [t.model_dump() for t in pending],
            "in_progress_tasks": [t.model_dump() for t in in_progress],
            "preferences": self._tasks.preferences.model_dump(),
            # 3. Notes — lowest priority, most recent 5 only
            "recent_notes": [n.model_dump() for n in self._notes[-5:]],
        }
