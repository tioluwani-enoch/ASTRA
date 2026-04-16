"""
Temporal Parsing Layer.

Converts natural language time expressions to ISO 8601 before task creation.
This runs BEFORE the state machine so no raw time strings ever reach Task objects.

Examples:
  "7 PM"         → "2026-04-15T19:00:00"
  "tomorrow"     → "2026-04-16"
  "next Friday"  → "2026-04-17"
  "April 20"     → "2026-04-20"
  "2026-04-20"   → "2026-04-20"  (pass-through)
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from utils.logger import get_logger

logger = get_logger(__name__)

# Fields that may contain temporal expressions
_TEMPORAL_KEYS = {"due_date", "time", "datetime", "date", "scheduled_at"}


def normalize(expression: str, reference: date | None = None) -> str | None:
    """
    Parse a natural language time expression into ISO 8601.
    Returns the original string if parsing fails (never raises).
    """
    if not expression or not expression.strip():
        return None

    ref = reference or date.today()
    lower = expression.strip().lower()

    # Fast path for already-normalized ISO strings
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            datetime.strptime(expression.strip(), fmt)
            return expression.strip()
        except ValueError:
            pass

    # Simple keyword shortcuts (dateutil handles these too, but explicit is faster)
    shortcuts: dict[str, date] = {
        "today":     ref,
        "tomorrow":  ref + relativedelta(days=1),
        "yesterday": ref + relativedelta(days=-1),
        "next week": ref + relativedelta(weeks=1),
    }
    if lower in shortcuts:
        return shortcuts[lower].isoformat()

    # Delegate to dateutil for everything else
    # Use a default datetime anchored to reference date so relative expressions work
    default_dt = datetime(ref.year, ref.month, ref.day, 0, 0, 0)
    try:
        parsed = dateutil_parser.parse(expression, default=default_dt)
        # Return datetime string if a time component was specified, date-only otherwise
        if parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
            return parsed.date().isoformat()
        return parsed.isoformat()
    except Exception as exc:
        logger.debug(f"[TEMPORAL] Could not parse {expression!r}: {exc}")
        return expression  # return original rather than None — don't silently drop user input


def normalize_params(params: dict[str, Any], reference: date | None = None) -> dict[str, Any]:
    """
    Normalize all temporal fields in an intent parameter dict in-place.
    Returns the same dict (mutated).
    """
    for key in _TEMPORAL_KEYS:
        if key in params and params[key]:
            raw = str(params[key])
            normalized = normalize(raw, reference)
            if normalized and normalized != raw:
                logger.info(f"[TEMPORAL] Normalized {key}: {raw!r} → {normalized!r}")
                params[key] = normalized
    return params
