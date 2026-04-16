import json
from pathlib import Path
from datetime import date

from memory.manager import MemoryManager
from memory.models import TaskStatus
from services.llm.anthropic import AnthropicService
from core.priority_engine import workload_summary

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")


class PlannerAgent:
    def __init__(self, memory: MemoryManager, llm: AnthropicService):
        self.memory = memory
        self.llm = llm

    def run(self, user_input: str) -> str:
        today = date.today()

        # Build priority-ranked workload — LLM receives scored, structured data
        # not a flat task dump
        all_tasks = self.memory.get_tasks()
        wl = workload_summary(all_tasks, today)

        # User profile for personalisation
        profile = self.memory.get_profile()
        prefs = self.memory.get_preferences()

        context = {
            "user": {
                "name":        profile.display_name(),
                "timezone":    profile.timezone or "local",
                "work_start":  prefs.work_start,
                "work_end":    prefs.work_end,
                "focus_block_minutes": prefs.focus_block_minutes,
                "break_minutes":       prefs.break_minutes,
            },
            "workload": wl,
        }

        system = (
            f"{PROMPT}\n\n"
            f"Today is {today.strftime('%A, %B %d %Y')}.\n\n"
            f"User context (pre-ranked by priority engine):\n"
            f"{json.dumps(context, indent=2)}"
        )
        messages = [{"role": "user", "content": user_input}]
        return self.llm.chat(system, messages)
