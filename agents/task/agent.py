import re
from memory.manager import MemoryManager
from memory.models import Priority


class TaskAgent:
    """Handles natural-language task commands without an LLM call."""

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def run(self, user_input: str) -> str:
        lower = user_input.lower()

        if "list" in lower:
            return self._list()
        if "add" in lower or "create" in lower:
            return self._add(user_input)
        if "remove" in lower or "delete" in lower:
            return self._remove(user_input)
        if "done" in lower or "complete" in lower or "finish" in lower:
            return self._complete(user_input)

        return "I'm not sure what you want to do with tasks. Try: add, list, done, or remove."

    def _list(self) -> str:
        tasks = self.memory.get_tasks()
        if not tasks:
            return "No tasks yet. Add one with: task add \"your task\""
        lines = [f"• [{t.priority.upper()}] {t.title} (id: {t.id}, status: {t.status})" for t in tasks]
        return "Your tasks:\n" + "\n".join(lines)

    def _add(self, user_input: str) -> str:
        # Extract quoted title or fall back to everything after "add"
        match = re.search(r'["\'](.+?)["\']', user_input)
        if match:
            title = match.group(1)
        else:
            title = re.sub(r"(?i)(add|create|task)\s*", "", user_input).strip()
        if not title:
            return "Please provide a task title."
        task = self.memory.add_task(title)
        return f"Task added: \"{task.title}\" (id: {task.id})"

    def _remove(self, user_input: str) -> str:
        task_id = self._extract_id(user_input)
        if not task_id:
            return "Please provide the task id to remove."
        removed = self.memory.remove_task(task_id)
        return f"Task {task_id} removed." if removed else f"No task found with id: {task_id}"

    def _complete(self, user_input: str) -> str:
        task_id = self._extract_id(user_input)
        if not task_id:
            return "Please provide the task id to mark as done."
        task = self.memory.complete_task(task_id)
        return f"Completed: \"{task.title}\"" if task else f"No task found with id: {task_id}"

    @staticmethod
    def _extract_id(text: str) -> str | None:
        # IDs are 8-char hex strings
        match = re.search(r'\b([a-f0-9]{8})\b', text)
        return match.group(1) if match else None
