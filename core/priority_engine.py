"""
Priority Engine — scores and ranks tasks for proactive planning.

Pure Python, no LLM. Runs before the Planner agent so the LLM receives
pre-ranked, pre-scored context rather than a flat task list.

Scoring formula:
  score = urgency * 0.60 + priority * 0.40

Urgency (due-date proximity):
  overdue        → 1.00
  due today      → 0.90
  due tomorrow   → 0.75
  within 3 days  → 0.55
  within 7 days  → 0.35
  no due date    → 0.10  (not forgotten, just flexible)

Priority weight:
  HIGH   → 1.00
  MEDIUM → 0.55
  LOW    → 0.20
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from memory.models import Task, TaskStatus, Priority
from utils.logger import get_logger

logger = get_logger(__name__)

_PRIORITY_WEIGHT = {Priority.HIGH: 1.00, Priority.MEDIUM: 0.55, Priority.LOW: 0.20}


@dataclass
class ScoredTask:
    task:          Task
    score:         float   # 0.0 – 1.0
    urgency:       float
    priority_w:    float
    days_until_due: int | None  # negative = overdue


def _parse_due(due_date: str | None) -> date | None:
    if not due_date:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(due_date, fmt).date()
        except ValueError:
            pass
    return None


def _urgency(due: date | None, today: date) -> tuple[float, int | None]:
    if due is None:
        return 0.10, None
    delta = (due - today).days
    if delta < 0:
        return 1.00, delta   # overdue
    if delta == 0:
        return 0.90, 0
    if delta == 1:
        return 0.75, 1
    if delta <= 3:
        return 0.55, delta
    if delta <= 7:
        return 0.35, delta
    return 0.15, delta


def score_task(task: Task, today: date | None = None) -> ScoredTask:
    today = today or date.today()
    due = _parse_due(task.due_date)
    urg, days = _urgency(due, today)
    pw = _PRIORITY_WEIGHT.get(task.priority, 0.55)
    final = round(urg * 0.60 + pw * 0.40, 3)
    return ScoredTask(task=task, score=final, urgency=urg, priority_w=pw, days_until_due=days)


def rank_tasks(tasks: list[Task], today: date | None = None) -> list[ScoredTask]:
    """Return tasks sorted highest score first."""
    today = today or date.today()
    scored = [score_task(t, today) for t in tasks]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def workload_summary(tasks: list[Task], today: date | None = None) -> dict[str, Any]:
    """
    Build a structured workload report for the planner LLM.
    This replaces the flat task dump — gives the LLM actionable intelligence.
    """
    today = today or date.today()
    active = [t for t in tasks if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)]
    scored = rank_tasks(active, today)

    overdue      = [s for s in scored if s.days_until_due is not None and s.days_until_due < 0]
    due_today    = [s for s in scored if s.days_until_due == 0]
    due_tomorrow = [s for s in scored if s.days_until_due == 1]
    due_week     = [s for s in scored if s.days_until_due is not None and 2 <= s.days_until_due <= 7]
    flexible     = [s for s in scored if s.days_until_due is None]

    priority_dist = {
        "high":   sum(1 for t in active if t.priority == Priority.HIGH),
        "medium": sum(1 for t in active if t.priority == Priority.MEDIUM),
        "low":    sum(1 for t in active if t.priority == Priority.LOW),
    }

    def fmt(s: ScoredTask) -> dict:
        return {
            "id":       s.task.id,
            "title":    s.task.title,
            "priority": s.task.priority.value,
            "score":    s.score,
            "due":      s.task.due_date or "flexible",
            "status":   s.task.status.value,
        }

    return {
        "today":             today.isoformat(),
        "total_active":      len(active),
        "priority_breakdown": priority_dist,
        "overdue":           [fmt(s) for s in overdue],
        "due_today":         [fmt(s) for s in due_today],
        "due_tomorrow":      [fmt(s) for s in due_tomorrow],
        "due_this_week":     [fmt(s) for s in due_week],
        "flexible":          [fmt(s) for s in flexible],
        "ranked_all":        [fmt(s) for s in scored],
    }
