import anthropic
from config.settings import settings
from .base import BaseLLMService


class AnthropicService(BaseLLMService):
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.astra_model

    def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        use_cache: bool = True,
        max_tokens: int = 4096,
    ) -> str:
        system: list[dict] = [{"type": "text", "text": system_prompt}]
        if use_cache:
            # Cache the system prompt — saves tokens on repeated calls with the same prompt
            system[0]["cache_control"] = {"type": "ephemeral"}

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text
