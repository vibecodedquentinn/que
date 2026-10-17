from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import chat_once, chat_stream
from app.config import settings
from app.memory import clear_session, init_db
from app.tools.devices import list_devices


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="JARVIS Home", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class StatusResponse(BaseModel):
    name: str
    llm_configured: bool
    model: str
    language: str


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    return StatusResponse(
        name=settings.jarvis_name,
        llm_configured=bool(settings.openai_api_key),
        model=settings.openai_model,
        language=settings.default_language,
    )


@app.get("/api/devices")
async def devices():
    raw = await list_devices()
    return json.loads(raw)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id or str(uuid.uuid4())
    reply = await chat_once(session_id, req.message)
    return ChatResponse(session_id=session_id, reply=reply)


@app.post("/api/session/{session_id}/clear")
async def clear(session_id: str) -> dict[str, bool]:
    await clear_session(session_id)
    return {"ok": True}


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    await websocket.send_json({"type": "session", "session_id": session_id})

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if payload.get("type") == "clear":
                await clear_session(session_id)
                await websocket.send_json({"type": "cleared"})
                continue

            message = (payload.get("message") or "").strip()
            if not message:
                continue

            async for event in chat_stream(session_id, message):
                await websocket.send_json(event)
    except WebSocketDisconnect:
        return
