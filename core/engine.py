"""
Core Engine — layered pipeline:

  User Input
       ↓
  [1] Conversation Layer    — confirmation check (resolve_confirmation)
       ↓
  [2] Entity + Temporal     — normalize dates, deduplicate tasks
       ↓
  [3] Intent Parser         — LLM → structured IntentResult
       ↓
  [4] Normalization Layer   — enum coercion before storage
       ↓
  [5] Operation Manager     — validate fields, gate on missing
       ↓
  [6] State Machine         — READY → EXECUTING → COMPLETED
       ↓
  [7] Response + History    — record turns, surface suggestions

Constraints:
  - Do NOT break existing tool interfaces
  - Do NOT remove state machine
  - Conversation layer must not interfere with normal intent parsing
  - Must fallback safely if no pending action exists
"""
from memory.manager import MemoryManager
from services.llm.anthropic import AnthropicService
from core.router import Router
from core.tool_registry import REGISTRY
from core.operation_manager import OperationManager
from core.operation import OperationStatus
from core.intent import IntentType
from core import temporal, entity_resolver
from core.conversation.memory import ConversationMemory
from core.conversation.resolver import resolve_confirmation
from core.normalization.enums import normalize_intent_params
from utils.logger import get_logger

logger = get_logger(__name__)


class Engine:
    def __init__(self):
        self.memory      = MemoryManager()
        self.llm         = AnthropicService()
        self.router      = Router(self.llm, self.memory)
        self.op_manager  = OperationManager()
        self.conv_memory = ConversationMemory()

    def handle(self, user_input: str) -> str:
        logger.debug(f"[INPUT] {user_input!r}")

        # ── Layer 1: Conversation — confirmation check ────────────────────────
        # Runs BEFORE intent parsing so "yeah" never reaches the LLM.
        pending = resolve_confirmation(self.conv_memory, user_input)
        if pending:
            logger.info(f"[CONFIRM] {pending.action} | target={pending.target_id}")
            op = self.op_manager.create_from_action(pending)
            self.conv_memory.clear()
            self.conv_memory.add_turn("user", user_input)

            handler = REGISTRY.get(IntentType(op.intent))
            if not handler:
                from api.responses import error as err_resp
                return err_resp(f"No handler for confirmed action \"{op.intent}\".")
            try:
                result = self.op_manager.execute_if_ready(
                    op,
                    lambda fields: handler(self.memory, self.llm, fields),
                )
                self.conv_memory.add_turn("assistant", result.message)
                return result
            except Exception as exc:
                logger.exception(f"[CONFIRM ERROR] {exc}")
                from api.responses import error as err_resp
                return err_resp("Something went wrong executing that. Check the logs.")

        # ── Layer 2a: AWAITING_INPUT continuation ─────────────────────────────
        if self.op_manager.has_pending():
            operation = self.op_manager.try_continue(user_input, self.llm)
            logger.info(f"[STATE] Continuing {operation.operation_id} | status={operation.status}")

        else:
            # ── Layer 2b: Intent Parser ───────────────────────────────────────
            intent_result = self.router.parse(user_input)
            logger.info(f"[INTENT] {intent_result.intent} | params={intent_result.parameters}")
            self.conv_memory.set_last_intent(intent_result.intent.value)

            # ── Layer 3: Temporal normalization ───────────────────────────────
            temporal.normalize_params(intent_result.parameters)

            # ── Layer 4: Entity resolution ────────────────────────────────────
            intent_result = entity_resolver.resolve(intent_result, self.memory)
            if intent_result.intent == IntentType.UPDATE_TASK:
                logger.info(f"[ENTITY] Resolved to update_task | params={intent_result.parameters}")

            # ── Layer 5: Enum normalization ───────────────────────────────────
            normalize_intent_params(intent_result.parameters)

            # ── Layer 6: Operation create ─────────────────────────────────────
            operation = self.op_manager.create(intent_result, user_input)

        # ── Execution Gate ────────────────────────────────────────────────────
        from api.responses import error as err_resp, awaiting_input as await_resp
        if operation.status == OperationStatus.AWAITING_INPUT:
            prompt = self.op_manager.prompt_for_missing()
            logger.info(f"[GATE] Blocked | missing={operation.missing_fields}")
            return await_resp(prompt, operation.missing_fields)

        # ── Route to handler ──────────────────────────────────────────────────
        handler = REGISTRY.get(IntentType(operation.intent))
        if not handler:
            self.op_manager.fail_active("no handler registered")
            logger.error(f"[NO HANDLER] {operation.intent}")
            return err_resp(f"I don't know how to handle \"{operation.intent}\" yet.")

        # Pass conv_memory to GENERAL_CHAT so it can read history and store suggestions
        if IntentType(operation.intent) == IntentType.GENERAL_CHAT:
            operation.provided_fields["_conv_memory"] = self.conv_memory

        try:
            result = self.op_manager.execute_if_ready(
                operation,
                lambda fields: handler(self.memory, self.llm, fields),
            )
        except ValueError as exc:
            logger.error(f"[GATE VIOLATION] {exc}")
            return err_resp("I need more information before I can do that.")
        except Exception as exc:
            logger.exception(f"[EXECUTION ERROR] {exc}")
            self.op_manager.fail_active(str(exc))
            return err_resp("Something went wrong. Check the logs.")

        # ── Layer 7: Record turns in conversation history ─────────────────────
        self.conv_memory.add_turn("user", user_input)
        self.conv_memory.add_turn("assistant", result.message)

        logger.debug(f"[RESULT] type={result.type} msg={result.message[:80]!r}")
        return result
