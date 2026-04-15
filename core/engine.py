from memory.manager import MemoryManager
from services.llm.anthropic import AnthropicService
from core.router import route, Intent
from core import context as ctx


class Engine:
    def __init__(self):
        self.memory = MemoryManager()
        self.llm = AnthropicService()

    def handle(self, user_input: str) -> str:
        intent = route(user_input)

        if intent == Intent.PLAN:
            from agents.planner.agent import PlannerAgent
            return PlannerAgent(self.memory, self.llm).run(user_input)

        if intent == Intent.REFLECT:
            from agents.reflection.agent import ReflectionAgent
            return ReflectionAgent(self.memory, self.llm).run(user_input)

        if intent == Intent.TASK:
            from agents.task.agent import TaskAgent
            return TaskAgent(self.memory).run(user_input)

        if intent == Intent.NOTE:
            # Quick note — extract content and save
            content = user_input.strip()
            for prefix in ("note ", "remember ", "jot ", "write down "):
                if content.lower().startswith(prefix):
                    content = content[len(prefix):]
                    break
            note = self.memory.add_note(content)
            return f"Note saved: \"{note.content}\""

        # Fallback: send raw input to LLM with memory context
        memory_context = ctx.build_context(self.memory)
        messages = [{"role": "user", "content": user_input}]
        system = (
            "You are Astra, a personal AI Chief of Staff. "
            "You help the user plan their day, manage tasks, and reflect on progress.\n\n"
            f"Current user context:\n{memory_context}"
        )
        return self.llm.chat(system, messages)
