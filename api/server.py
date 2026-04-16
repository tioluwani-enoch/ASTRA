"""
Astra API Server — thin FastAPI wrapper over the existing engine.

Rules (from FRONTEND_NEXT_STEP.md):
  - Do NOT rewrite backend
  - Do NOT add auth
  - Keep it simple

/chat  — text message → engine.handle() → ChatResponse
/action — structured button click → direct handler execution, no LLM parsing
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.engine import Engine
from core.types import ChatResponse

app = FastAPI(title="Astra", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

_FRONTEND = Path(__file__).parent.parent / "frontend"
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND)), name="static")

# Single engine instance — carries conversation memory across requests
_engine = Engine()


# ── Request models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ActionRequest(BaseModel):
    type:    str
    payload: dict[str, Any] = {}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    html = _FRONTEND / "index.html"
    if html.exists():
        return FileResponse(str(html))
    return {"status": "Astra API running. No frontend found."}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """
    Main text interaction endpoint.

    Accepts: { "message": "..." }
    Returns: ChatResponse  (type, message, actions, data, ui)
    """
    return _engine.handle(req.message)


@app.post("/action", response_model=ChatResponse)
def action(req: ActionRequest) -> ChatResponse:
    """
    Structured action endpoint — used by frontend buttons.

    Bypasses LLM intent parsing entirely.
    type='cancel' is a no-op that returns a chat acknowledgement.

    Accepts: { "type": "complete_task", "payload": {"task_id": "abc123"} }
    Returns: ChatResponse
    """
    from core.tool_registry import REGISTRY
    from core.intent import IntentType
    from api.responses import chat as chat_resp, error as error_resp

    if req.type == "cancel":
        return chat_resp("OK, no action taken.")

    try:
        intent   = IntentType(req.type)
        handler  = REGISTRY.get(intent)
        if not handler:
            return error_resp(f"No handler registered for action \"{req.type}\".")
        return handler(_engine.memory, _engine.llm, req.payload)
    except ValueError:
        return error_resp(f"Unknown action type: \"{req.type}\".")
    except Exception as exc:
        return error_resp(f"Action failed: {exc}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
