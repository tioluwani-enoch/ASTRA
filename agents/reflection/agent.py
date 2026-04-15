from pathlib import Path
from datetime import date

from memory.manager import MemoryManager
from services.llm.anthropic import AnthropicService
from core.context import build_context

PROMPT = (Path(__file__).parent / "prompt.txt").read_text(encoding="utf-8")


class ReflectionAgent:
    def __init__(self, memory: MemoryManager, llm: AnthropicService):
        self.memory = memory
        self.llm = llm

    def run(self, user_input: str) -> str:
        memory_context = build_context(self.memory)
        today = date.today().strftime("%A, %B %d %Y")

        system = f"{PROMPT}\n\nToday is {today}.\n\nUser context:\n{memory_context}"
        messages = [{"role": "user", "content": user_input}]
        return self.llm.chat(system, messages)
