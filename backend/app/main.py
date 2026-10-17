from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent import chat_once, chat_stream
from app.config import settings
from app.integrations import fritzbox as fb
from app.integrations import homeassistant as ha
from app.memory import clear_session, init_db
from app.tools.devices import control_device, list_devices
from app.tts import tts_response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="J.Ü.R.G.E.N.", version="1.2.0", lifespan=lifespan)

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


class DeviceControlRequest(BaseModel):
    action: str = Field(pattern=r"^(on|off|toggle|set)$")
    value: str | None = None


class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class StatusResponse(BaseModel):
    name: str
    acronym: str
    llm_configured: bool
    llm_backend: str
    model: str
    language: str
    smart_home_provider: str
    homeassistant_connected: bool
    fritzbox_connected: bool
    tts_provider: str
    public_url: str | None


STATIC_ROOT = Path(settings.static_dir)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    ha_ok = await ha.ping() if ha.configured() else False
    fb_ok = await fb.ping() if fb.configured() else False
    return StatusResponse(
        name=settings.assistant_name,
        acronym=settings.assistant_acronym,
        llm_configured=settings.llm_configured,
        llm_backend=settings.llm_backend_label,
        model=settings.effective_llm_model,
        language=settings.default_language,
        smart_home_provider=settings.smart_home_provider,
        homeassistant_connected=ha_ok,
        fritzbox_connected=fb_ok,
        tts_provider=settings.tts_provider,
        public_url=settings.effective_public_url,
    )


@app.get("/api/devices")
async def devices():
    raw = await list_devices()
    return json.loads(raw)


@app.post("/api/devices/{device_id}/control")
async def device_control(device_id: str, req: DeviceControlRequest):
    raw = await control_device(device_id, req.action, req.value)
    return json.loads(raw)


@app.post("/api/tts")
async def tts_post(req: TtsRequest):
    return await tts_response(req.text)


@app.get("/api/tts")
async def tts_get(text: str):
    return await tts_response(text)


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


def _mount_frontend() -> None:
    if not STATIC_ROOT.is_dir():
        return
    assets = STATIC_ROOT / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/manifest.webmanifest")
    async def manifest():
        path = STATIC_ROOT / "manifest.webmanifest"
        if path.is_file():
            return FileResponse(path, media_type="application/manifest+json")
        return FileResponse(STATIC_ROOT / "index.html")

    @app.get("/sw.js")
    async def service_worker():
        path = STATIC_ROOT / "sw.js"
        if path.is_file():
            return FileResponse(path, media_type="application/javascript")
        raise HTTPException(status_code=404, detail="Service worker not found")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return {"detail": "Not Found"}
        candidate = STATIC_ROOT / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index = STATIC_ROOT / "index.html"
        if index.is_file():
            return FileResponse(index)
        return {"detail": "Frontend not built. Run scripts/build-web.sh"}


_mount_frontend()
