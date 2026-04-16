from __future__ import annotations

from core.intent import IntentResult, IntentType
from core.context import build_context
from utils.logger import get_logger

logger = get_logger(__name__)


class Router:
    """
    Translates raw user input into a structured IntentResult.

    The LLM is forced to call the extract_intent tool (tool_choice enforced),
    so the output is always a validated schema — never free text.
    This layer has no fallback logic and no keyword guessing.
    """

    def __init__(self, llm, memory):
        self.llm = llm
        self.memory = memory

    def parse(self, user_input: str) -> IntentResult:
        context = build_context(self.memory)
        raw = self.llm.extract_intent(user_input, context)

        try:
            result = IntentResult.model_validate(raw)
        except Exception as exc:
            logger.warning(f"[ROUTER] Intent validation failed: {exc}. Falling back to general_chat.")
            result = IntentResult(
                intent=IntentType.GENERAL_CHAT,
                parameters={"message": user_input},
            )

        logger.debug(f"[ROUTER] {result}")
        return result
