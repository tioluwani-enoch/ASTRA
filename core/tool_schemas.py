"""
Tool schemas — defines required and optional fields for each intent.

The state machine uses these to determine whether an operation can execute
immediately (all required fields present) or must pause and ask for input.

required: fields that MUST be provided before execution is allowed
optional: fields that improve behaviour but are not blocking
"""

TOOL_SCHEMAS: dict[str, dict[str, list[str]]] = {
    # ── Fire-and-forget (no required fields) ──────────────────────────────────
    "plan_day":    {"required": [],          "optional": []},
    "reflect":     {"required": [],          "optional": []},
    "list_tasks":  {"required": [],          "optional": ["status"]},
    "get_profile": {"required": [],          "optional": ["key"]},

    # ── Task management ───────────────────────────────────────────────────────
    "add_task":      {"required": ["title"],  "optional": ["priority", "due_date", "description"]},
    "update_task":   {"required": [],         "optional": ["task_id", "title", "new_title", "priority", "due_date", "status", "description"]},
    # complete/remove need task_id OR title — handlers deal with the either/or;
    # state machine doesn't gate on them (both are effectively optional here)
    "complete_task": {"required": [],         "optional": ["task_id", "title"]},
    "remove_task":   {"required": [],         "optional": ["task_id", "title"]},

    # ── Memory ────────────────────────────────────────────────────────────────
    "add_note":      {"required": ["content"],         "optional": []},
    "update_profile":{"required": ["key", "value"],    "optional": []},

    # ── File system ───────────────────────────────────────────────────────────
    "create_file":   {"required": ["filename", "content"], "optional": ["author", "file_type"]},
    "read_file":     {"required": ["filename"],            "optional": []},
    "update_file":   {"required": ["filename", "content"], "optional": []},

    # ── Fallback ──────────────────────────────────────────────────────────────
    "general_chat":  {"required": ["message"], "optional": []},
}
