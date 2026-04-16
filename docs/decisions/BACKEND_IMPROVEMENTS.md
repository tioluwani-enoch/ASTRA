# 🧠 Astra — Backend Stabilization Plan

## Goal
Make backend consistent and reliable.

## Fix 1 — Profile Keys
Use ONLY:
- full_name
- preferred_name

## Fix 2 — Update Task Bug
Use unified payload:

{
  "task_id": str,
  "updates": {
    "title": str,
    "priority": str,
    "due_date": str
  }
}

## Fix 3 — Enum Normalization

def normalize_priority(value):
    return Priority[value.upper()]

## Fix 4 — Deduplication

if task_exists(title):
    return "Task already exists"

## Fix 5 — Fuzzy Matching

from difflib import get_close_matches

## Fix 6 — Middleware

def process_input(input):
    input = normalize_text(input)
    intent = parse_intent(input)
    return execute(intent)

## Priority
1. Fix update_task
2. Normalize profile
3. Fix enums
