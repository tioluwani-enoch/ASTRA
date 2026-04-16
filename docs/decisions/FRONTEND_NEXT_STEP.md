# 🚀 Astra — Frontend Integration (Thin Layer)

## Goal
Expose the existing CLI engine through a web interface with **zero backend rewrites**.

## Architecture
Frontend → FastAPI → Engine → Operations → State Machine

## Step 1 — API Wrapper
Create: api/server.py

from fastapi import FastAPI
from pydantic import BaseModel
from core.engine import process_input

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    return {"response": process_input(req.message)}

## Step 2 — Run
uvicorn api.server:app --reload

## Step 3 — Minimal Frontend
- Input box
- Chat display
- POST to /chat
- Render response

## Rules
- Do NOT rewrite backend
- Do NOT add auth
- Keep it simple

## Done When
Browser input → backend → Astra response works
