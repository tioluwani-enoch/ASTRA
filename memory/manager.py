from .models import MemoryStore, Task, Note, Preferences, TaskStatus, Priority
from . import store as _store


class MemoryManager:
    def __init__(self):
        self._data: MemoryStore = _store.load()

    def _save(self) -> None:
        _store.save(self._data)

    # --- Tasks ---

    def add_task(self, title: str, description: str = "", priority: Priority = Priority.MEDIUM, due_date: str | None = None) -> Task:
        task = Task(title=title, description=description, priority=priority, due_date=due_date)
        self._data.tasks.append(task)
        self._save()
        return task

    def get_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        if status is None:
            return list(self._data.tasks)
        return [t for t in self._data.tasks if t.status == status]

    def complete_task(self, task_id: str) -> Task | None:
        for task in self._data.tasks:
            if task.id == task_id:
                task.complete()
                self._save()
                return task
        return None

    def remove_task(self, task_id: str) -> bool:
        before = len(self._data.tasks)
        self._data.tasks = [t for t in self._data.tasks if t.id != task_id]
        if len(self._data.tasks) < before:
            self._save()
            return True
        return False

    # --- Notes ---

    def add_note(self, content: str) -> Note:
        note = Note(content=content)
        self._data.notes.append(note)
        self._save()
        return note

    def get_notes(self) -> list[Note]:
        return list(self._data.notes)

    # --- Preferences ---

    def get_preferences(self) -> Preferences:
        return self._data.preferences

    def update_preference(self, key: str, value: str) -> None:
        prefs = self._data.preferences
        if hasattr(prefs, key):
            setattr(prefs, key, value)
        else:
            prefs.extras[key] = value
        self._save()

    # --- Snapshot for LLM context ---

    def context_snapshot(self) -> dict:
        """Returns a serializable summary for injecting into LLM context."""
        pending = self.get_tasks(TaskStatus.TODO)
        in_progress = self.get_tasks(TaskStatus.IN_PROGRESS)
        return {
            "pending_tasks": [t.model_dump() for t in pending],
            "in_progress_tasks": [t.model_dump() for t in in_progress],
            "recent_notes": [n.model_dump() for n in self._data.notes[-5:]],
            "preferences": self._data.preferences.model_dump(),
        }
