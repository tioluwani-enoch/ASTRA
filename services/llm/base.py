from abc import ABC, abstractmethod


class BaseLLMService(ABC):
    @abstractmethod
    def chat(self, system_prompt: str, messages: list[dict], use_cache: bool = True) -> str:
        """Send a conversation to the LLM and return the response text."""
        ...
