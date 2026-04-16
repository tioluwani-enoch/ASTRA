import anthropic
from config.settings import settings
from .base import BaseLLMService
from typing import Any

# Intent type values — kept as literals here to avoid a circular import with core.intent
_INTENT_VALUES = [
    "plan_day", "reflect",
    "add_task", "update_task", "list_tasks", "complete_task", "remove_task",
    "add_note",
    "update_profile", "get_profile",
    "create_file", "read_file", "update_file",
    "general_chat",
]

_EXTRACT_INTENT_TOOL = {
    "name": "extract_intent",
    "description": (
        "Extract the user's intent and any relevant parameters from their message. "
        "Always call this tool — never respond in free text.\n\n"
        "CRITICAL CLASSIFICATION RULES — these are mandatory and override all other reasoning:\n"
        "1. IDENTITY: If the user provides or asks about their name, email, timezone, or any personal "
        "   identity fact → use update_profile or get_profile. NEVER store identity as add_note.\n"
        "2. FILES: If the user mentions 'file', 'markdown', '.md', '.txt', '.json', 'document', "
        "   'save as', or any file extension → intent MUST be create_file / read_file / update_file. "
        "   NEVER classify file requests as add_note.\n"
        "3. NOTES: add_note is ONLY for lightweight, ephemeral entries — ideas, reminders, observations. "
        "   Not for identity, not for files, not for tasks.\n"
        "4. Preserve ALL user-provided metadata: names, filenames, file types, authors."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": _INTENT_VALUES,
                "description": (
                    "The primary intent of the user's message. "
                    "Use plan_day for: 'plan my day', 'what should I do today', 'what should I focus on', "
                    "'what's my schedule', 'prioritize my tasks', 'what's most important right now'. "
                    "Use create_file for any request involving a file, markdown, or document — NOT add_note."
                ),
            },
            "parameters": {
                "type": "object",
                "description": (
                    "All parameters extracted from the message. Preserve every entity the user mentions.\n"
                    "add_task: title (required), priority (low/medium/high), due_date (natural language or YYYY-MM-DD), description.\n"
                    "update_task: task_id or title (to identify task), then any fields to change: new_title (rename), priority, due_date, status, description.\n"
                    "complete_task / remove_task: task_id or title.\n"
                    "list_tasks: status (pending/done/all).\n"
                    "add_note: content (ephemeral thoughts/ideas only — not identity, not files).\n"
                    "update_profile: key (full_name/preferred_name/email/timezone or custom), value.\n"
                    "get_profile: key (the field the user is asking about, e.g. 'name', 'email').\n"
                    "create_file: filename (required, infer from context if not explicit), "
                    "content (required), author (if mentioned), file_type (md/txt/json).\n"
                    "read_file: filename (required).\n"
                    "update_file: filename (required), content (required).\n"
                    "general_chat: message."
                ),
            },
        },
        "required": ["intent", "parameters"],
    },
}


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
            system[0]["cache_control"] = {"type": "ephemeral"}

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    def extract_intent(self, user_input: str, context: str) -> dict:
        """
        Force the LLM to output a structured intent via tool use.
        The model cannot respond in free text — it must call extract_intent.
        This is the ONLY place the LLM participates in routing decisions.
        """
        system: list[dict] = [
            {
                "type": "text",
                "text": (
                    "You are Astra's intent parser. Your only job is to call the "
                    "extract_intent tool with the correct intent and parameters. "
                    "Never respond in free text.\n\n"
                    f"Current user context:\n{context}"
                ),
                "cache_control": {"type": "ephemeral"},
            }
        ]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=system,
            tools=[_EXTRACT_INTENT_TOOL],
            tool_choice={"type": "tool", "name": "extract_intent"},
            messages=[{"role": "user", "content": user_input}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "extract_intent":
                return block.input  # type: ignore[return-value]

        # Should never reach here given tool_choice is forced, but safe fallback
        return {"intent": "general_chat", "parameters": {"message": user_input}}

    def extract_fields(
        self,
        user_input: str,
        missing_fields: list[str],
        operation_context: dict,
    ) -> dict:
        """
        Extract specific missing fields from a continuation message.
        Called only when there is an active AWAITING_INPUT operation.

        Uses tool_choice to force structured output — only the listed fields
        are extracted. The LLM cannot add fields or change intent.
        """
        if not missing_fields:
            return {}

        tool = {
            "name": "provide_fields",
            "description": (
                f"The user is continuing a '{operation_context.get('intent', 'operation')}' operation. "
                f"Original request: \"{operation_context.get('original_request', '')}\". "
                f"Extract these missing fields from their follow-up message: {missing_fields}. "
                "Only extract fields that are clearly provided. Leave others absent."
            ),
            "input_schema": {
                "type": "object",
                "properties": {field: {"type": "string"} for field in missing_fields},
                "required": [],  # none required — user may provide only some
            },
        }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            tools=[tool],
            tool_choice={"type": "tool", "name": "provide_fields"},
            messages=[{"role": "user", "content": user_input}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "provide_fields":
                return {k: v for k, v in block.input.items() if v}

        return {}

    def chat_with_actions(
        self,
        system_prompt: str,
        messages: list[dict],
        use_cache: bool = True,
    ) -> tuple[str, dict[str, Any] | None]:
        """
        General chat that can optionally return a suggested executable action.

        Returns (response_text, suggested_action_or_None).
        suggested_action has shape: {intent, parameters, description}.

        The LLM is forced to call generate_response — it cannot respond in
        free text. This guarantees the suggestion is always structured.
        """
        _tool = {
            "name": "generate_response",
            "description": (
                "Generate a conversational reply to the user. "
                "If you want to suggest a specific Astra action (e.g. mark a task complete, "
                "add a task, update something), include it in suggested_action so the user "
                "can confirm with a single word. Only suggest one action at a time. "
                "Leave suggested_action absent if no specific action applies."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "The reply text to show the user.",
                    },
                    "suggested_action": {
                        "type": "object",
                        "description": (
                            "Optional: a single Astra action the user can confirm. "
                            "Omit entirely when no clear action applies."
                        ),
                        "properties": {
                            "intent": {
                                "type": "string",
                                "enum": _INTENT_VALUES,
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Parameters for the action (same as extract_intent).",
                            },
                            "description": {
                                "type": "string",
                                "description": "Short label shown to user, e.g. \"mark 'Buy milk' as done\".",
                            },
                        },
                        "required": ["intent", "parameters", "description"],
                    },
                },
                "required": ["response"],
            },
        }

        system: list[dict] = [{"type": "text", "text": system_prompt}]
        if use_cache:
            system[0]["cache_control"] = {"type": "ephemeral"}

        api_response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            tools=[_tool],
            tool_choice={"type": "tool", "name": "generate_response"},
            messages=messages,
        )

        for block in api_response.content:
            if block.type == "tool_use" and block.name == "generate_response":
                text = block.input.get("response", "")
                action = block.input.get("suggested_action")
                return text, action

        # Fallback — should never occur with forced tool_choice
        return "", None
