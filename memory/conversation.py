# Compatibility shim — conversation logic lives in core/conversation/.
# Nothing in the codebase imports from here after the refactor, but
# keeping this prevents import errors if any external script does.
from core.conversation.models import PendingAction, Turn, ConversationState
from core.conversation.memory import ConversationMemory
from core.conversation.resolver import is_confirmation, resolve_confirmation

__all__ = [
    "PendingAction", "Turn", "ConversationState",
    "ConversationMemory",
    "is_confirmation", "resolve_confirmation",
]
