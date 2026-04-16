"""
Tool Registry — deterministic execution layer.

Rules:
  - No LLM logic in this file.
  - Each handler receives validated parameters and performs the real action.
  - Handlers for plan/reflect/general_chat delegate to agents (which call the LLM).
  - Files and notes are STRICTLY separate.
  - All handlers return a structured response dict via api.responses builders.
"""
from __future__ import annotations

from typing import Any, Callable

from memory.manager import MemoryManager
from memory.models import Priority, TaskStatus
from core.intent import IntentType
from api.responses import (
    build_response, chat, task_created, task_updated, task_list, error,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Handler signature: (memory, llm, parameters) -> dict
Handler = Callable[[MemoryManager, Any, dict[str, Any]], dict]


# ── Enum normalization helpers ────────────────────────────────────────────────

def _coerce_priority(value: str | None) -> Priority | None:
    if not value:
        return None
    try:
        return Priority(value.strip().lower())
    except ValueError:
        try:
            return Priority[value.strip().upper()]
        except KeyError:
            return None


def _coerce_status(value: str | None) -> TaskStatus | None:
    if not value:
        return None
    try:
        return TaskStatus(value.strip().lower())
    except ValueError:
        try:
            return TaskStatus[value.strip().upper()]
        except KeyError:
            return None


# ── Task handlers ─────────────────────────────────────────────────────────────

def handle_add_task(memory: MemoryManager, _llm, params: dict) -> dict:
    title = params.get("title", "").strip()
    if not title:
        return error("I need a task title. Try: add task \"your task title\"")

    priority    = _coerce_priority(params.get("priority")) or Priority.MEDIUM
    due_date    = params.get("due_date") or None
    description = params.get("description", "")

    t = memory.add_task(title, description, priority, due_date)
    due_str = f", due {t.due_date}" if t.due_date else ""
    return task_created(
        f"Task added: \"{t.title}\" [{t.priority.value}]{due_str}",
        t,
    )


def handle_update_task(memory: MemoryManager, _llm, params: dict) -> dict:
    from core.entity_resolver import find_similar_task

    task_id   = params.get("task_id", "").strip()
    title     = params.get("title", "").strip()
    new_title = params.get("new_title", "").strip()

    task = None
    if task_id:
        task = next((t for t in memory.get_tasks() if t.id == task_id), None)
    if not task and title:
        active = memory.get_tasks(TaskStatus.TODO) + memory.get_tasks(TaskStatus.IN_PROGRESS)
        task = find_similar_task(title, active)
    if not task:
        return error("Task not found. Use `task list` to see current tasks.")

    updates: dict[str, Any] = {}
    if new_title:
        updates["title"] = new_title
    if params.get("priority"):
        coerced = _coerce_priority(params["priority"])
        if coerced:
            updates["priority"] = coerced
    if params.get("due_date"):
        updates["due_date"] = params["due_date"]
    if params.get("status"):
        coerced_status = _coerce_status(params["status"])
        if coerced_status:
            updates["status"] = coerced_status
    if params.get("description"):
        updates["description"] = params["description"]

    if not updates:
        return error(f"No changes specified for \"{task.title}\". Provide at least one field to update.")

    memory.update_task(task.id, **updates)
    old_title     = task.title
    current_title = updates.get("title", old_title)
    changes_str   = ", ".join(
        f"{k}={v.value if hasattr(v, 'value') else v}" for k, v in updates.items()
    )
    msg = (
        f"Task updated: \"{old_title}\" → \"{current_title}\" — {changes_str}"
        if new_title else
        f"Task updated: \"{old_title}\" — {changes_str}"
    )
    changes_serializable = {
        k: (v.value if hasattr(v, "value") else v) for k, v in updates.items()
    }
    return task_updated(msg, task.id, changes_serializable)


def handle_list_tasks(memory: MemoryManager, _llm, params: dict) -> dict:
    status_raw = params.get("status", "pending")
    if status_raw == "all":
        tasks = memory.get_tasks()
    elif status_raw == "done":
        tasks = memory.get_tasks(TaskStatus.DONE)
    else:
        tasks = memory.get_tasks(TaskStatus.TODO)

    if not tasks:
        return chat("No tasks found.")

    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    tasks.sort(key=lambda t: priority_order.get(t.priority, 1))
    return task_list(f"{len(tasks)} task(s) found.", tasks)


def handle_complete_task(memory: MemoryManager, _llm, params: dict) -> dict:
    task_id = params.get("task_id", "").strip()
    title   = params.get("title", "").strip()

    if task_id:
        t = memory.complete_task(task_id)
        if t:
            return task_updated(f"Completed: \"{t.title}\"", t.id, {"status": "done"})

    if title:
        all_tasks = memory.get_tasks(TaskStatus.TODO)
        match = next((t for t in all_tasks if title.lower() in t.title.lower()), None)
        if match:
            t = memory.complete_task(match.id)
            if t:
                return task_updated(f"Completed: \"{t.title}\"", t.id, {"status": "done"})

    return error("Task not found. Use `task list` to see ids.")


def handle_remove_task(memory: MemoryManager, _llm, params: dict) -> dict:
    task_id = params.get("task_id", "").strip()
    title   = params.get("title", "").strip()

    if task_id and memory.remove_task(task_id):
        return chat(f"Task {task_id} removed.")

    if title:
        all_tasks = memory.get_tasks()
        match = next((t for t in all_tasks if title.lower() in t.title.lower()), None)
        if match and memory.remove_task(match.id):
            return chat(f"Removed: \"{match.title}\"")

    return error("Task not found. Use `task list` to see ids.")


def handle_add_note(memory: MemoryManager, _llm, params: dict) -> dict:
    content = params.get("content", "").strip()
    if not content:
        return error("Note is empty — nothing saved.")
    note = memory.add_note(content)
    return chat(f"Note saved: \"{note.content}\"")


# ── Profile handlers ──────────────────────────────────────────────────────────

def handle_update_profile(memory: MemoryManager, _llm, params: dict) -> dict:
    key   = params.get("key", "").strip().lower().replace(" ", "_")
    value = params.get("value", "").strip()

    if not key:
        return error("I need a profile field to update (e.g. full_name, preferred_name, email).")
    if not value:
        return error(f"I need a value for '{key}'.")

    memory.update_profile(key, value)
    return chat(f"Profile updated: {key} = \"{value}\"")


def handle_get_profile(memory: MemoryManager, _llm, params: dict) -> dict:
    key = params.get("key", "").strip().lower().replace(" ", "_")

    if not key:
        profile = memory.get_profile()
        if profile.is_empty():
            return chat("No profile information saved yet. Try: my name is ...")
        lines = []
        if profile.full_name:      lines.append(f"Full name:      {profile.full_name}")
        if profile.preferred_name: lines.append(f"Preferred name: {profile.preferred_name}")
        if profile.email:          lines.append(f"Email:          {profile.email}")
        if profile.timezone:       lines.append(f"Timezone:       {profile.timezone}")
        for k, v in profile.extras.items():
            lines.append(f"{k}: {v}")
        return chat("Your profile:\n" + "\n".join(lines))

    value = memory.get_profile_field(key)
    if value:
        return chat(f"{key}: {value}")
    return chat(f"No profile entry for '{key}'. You can set it with: my {key} is ...")


# ── File system handlers ──────────────────────────────────────────────────────

def handle_create_file(_memory: MemoryManager, _llm, params: dict) -> dict:
    from actions.files import create_file

    filename = params.get("filename", "").strip()
    content  = params.get("content", "").strip()
    author   = params.get("author", "").strip()

    if not filename:
        return error("I need a filename. Try: create file ideas.md")
    if not content:
        return error("I need some content to put in the file.")

    if author and author not in content:
        content = f"Author: {author}\n\n{content}"
    if "." not in filename:
        filename = f"{filename}.md"

    try:
        path = create_file(filename, content)
        return chat(f"File created: {path.name}\nLocation: {path}")
    except FileExistsError as e:
        return error(str(e))
    except ValueError as e:
        return error(f"Cannot create file: {e}")


def handle_read_file(_memory: MemoryManager, _llm, params: dict) -> dict:
    from actions.files import read_file

    filename = params.get("filename", "").strip()
    if not filename:
        return error("I need a filename to read.")

    try:
        content = read_file(filename)
        return chat(f"--- {filename} ---\n{content}")
    except FileNotFoundError as e:
        return error(str(e))
    except ValueError as e:
        return error(f"Cannot read file: {e}")


def handle_update_file(_memory: MemoryManager, _llm, params: dict) -> dict:
    from actions.files import update_file

    filename = params.get("filename", "").strip()
    content  = params.get("content", "").strip()

    if not filename:
        return error("I need a filename to update.")
    if not content:
        return error("I need the new content for the file.")

    try:
        path = update_file(filename, content)
        return chat(f"File updated: {path.name}")
    except FileNotFoundError as e:
        return error(str(e))
    except ValueError as e:
        return error(f"Cannot update file: {e}")


# ── LLM-delegating handlers ───────────────────────────────────────────────────

def handle_plan_day(memory: MemoryManager, llm, _params: dict) -> dict:
    from agents.planner.agent import PlannerAgent
    text = PlannerAgent(memory, llm).run("plan my day")
    return chat(text)


def handle_reflect(memory: MemoryManager, llm, _params: dict) -> dict:
    from agents.reflection.agent import ReflectionAgent
    text = ReflectionAgent(memory, llm).run("reflect on today")
    return chat(text)


def handle_general_chat(memory: MemoryManager, llm, params: dict) -> dict:
    from core.context import build_context
    from api.responses import confirmation as conf_response

    message     = params.get("message", "")
    conv_memory = params.get("_conv_memory")

    memory_context = build_context(memory)
    history_block  = ""
    if conv_memory:
        summary = conv_memory.recent_summary()
        if summary:
            history_block = f"\n\nRecent conversation:\n{summary}"

    system = (
        "You are Astra, a personal AI Chief of Staff. "
        "Help the user plan, manage tasks, and reflect on their work. "
        "When relevant, suggest a concrete follow-up action the user can confirm.\n\n"
        f"Current user context:\n{memory_context}"
        f"{history_block}"
    )

    prior    = conv_memory.as_messages() if conv_memory else []
    messages = prior + [{"role": "user", "content": message}]

    response_text, suggested_action = llm.chat_with_actions(system, messages)

    if conv_memory and suggested_action:
        intent      = suggested_action.get("intent", "")
        sa_params   = suggested_action.get("parameters", {})
        description = suggested_action.get("description", "")
        target_id   = sa_params.pop("task_id", None)
        conv_memory.set_pending_action(
            action=intent,
            target_id=target_id,
            payload={**sa_params, "description": description},
        )
        # Return a confirmation response so the frontend can render yes/no buttons
        return conf_response(
            message=f"{response_text}\n\n→ Want me to {description}?",
            action=intent,
            task_id=target_id,
            payload=sa_params,
        )
    elif conv_memory:
        conv_memory.clear()

    return chat(response_text)


# ── Registry ──────────────────────────────────────────────────────────────────

REGISTRY: dict[IntentType, Handler] = {
    IntentType.PLAN_DAY:       handle_plan_day,
    IntentType.REFLECT:        handle_reflect,
    IntentType.ADD_TASK:       handle_add_task,
    IntentType.UPDATE_TASK:    handle_update_task,
    IntentType.LIST_TASKS:     handle_list_tasks,
    IntentType.COMPLETE_TASK:  handle_complete_task,
    IntentType.REMOVE_TASK:    handle_remove_task,
    IntentType.ADD_NOTE:       handle_add_note,
    IntentType.UPDATE_PROFILE: handle_update_profile,
    IntentType.GET_PROFILE:    handle_get_profile,
    IntentType.CREATE_FILE:    handle_create_file,
    IntentType.READ_FILE:      handle_read_file,
    IntentType.UPDATE_FILE:    handle_update_file,
    IntentType.GENERAL_CHAT:   handle_general_chat,
}
