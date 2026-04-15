import json
from memory.manager import MemoryManager


def build_context(memory: MemoryManager) -> str:
    """Serialise the current memory snapshot into a string for the LLM."""
    snapshot = memory.context_snapshot()
    return json.dumps(snapshot, indent=2)
