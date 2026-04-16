"""
Entity Resolver — Task Identity + Intent Disambiguation.

Fixes two related issues (from engineer-fix-errors.md):
  1. Task Duplication — same logical task created multiple times
  2. CREATE vs UPDATE ambiguity — add_task when user means update

Pipeline position:
  Intent Parser → Entity Resolver → Temporal Parser → State Machine → Execution

Rules:
  - If intent is add_task and a similar active task exists → redirect to update_task
  - Similarity is computed via SequenceMatcher ratio (stdlib, no extra deps)
  - Threshold of 0.80 — high enough to avoid false matches, low enough to catch typos
  - Never silently drop the original request; always log the decision
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from memory.models import Task, TaskStatus
from utils.logger import get_logger

if TYPE_CHECKING:
    from core.intent import IntentResult, IntentType
    from memory.manager import MemoryManager

logger = get_logger(__name__)

SIMILARITY_THRESHOLD = 0.80  # tune if needed


def find_similar_task(title: str, tasks: list[Task]) -> Task | None:
    """
    Return the task with the highest title similarity above SIMILARITY_THRESHOLD.
    Uses difflib.SequenceMatcher — no external library required.
    """
    if not title or not tasks:
        return None

    best_ratio = 0.0
    best_task: Task | None = None

    for task in tasks:
        ratio = SequenceMatcher(None, title.lower(), task.title.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_task = task

    if best_ratio >= SIMILARITY_THRESHOLD:
        logger.debug(f"[ENTITY] Match: {title!r} ~ {best_task.title!r} (ratio={best_ratio:.2f})")
        return best_task

    return None


def resolve(intent_result: IntentResult, memory: MemoryManager) -> IntentResult:
    """
    Inspect an add_task IntentResult and redirect to update_task if a duplicate exists.

    Returns the original IntentResult unchanged for all other intents, or when
    no similar task is found.
    """
    from core.intent import IntentResult as IR, IntentType

    if intent_result.intent != IntentType.ADD_TASK:
        return intent_result

    title = intent_result.parameters.get("title", "").strip()
    if not title:
        return intent_result

    active_tasks = (
        memory.get_tasks(TaskStatus.TODO)
        + memory.get_tasks(TaskStatus.IN_PROGRESS)
    )
    existing = find_similar_task(title, active_tasks)

    if existing:
        logger.info(
            f"[ENTITY] Redirecting add_task → update_task | "
            f"matched '{existing.title}' (id={existing.id})"
        )
        new_params = dict(intent_result.parameters)
        new_params["task_id"] = existing.id
        # Keep 'title' in params so the handler knows what changed
        return IR(intent=IntentType.UPDATE_TASK, parameters=new_params)

    return intent_result
