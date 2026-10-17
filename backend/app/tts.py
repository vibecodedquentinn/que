from __future__ import annotations

import io
import re

import httpx
from fastapi import HTTPException
from fastapi.responses import Response

from app.config import settings

MAX_TTS_CHARS = 2000


def _clean_text(text: str) -> str:
    t = text.strip()
    if len(t) > MAX_TTS_CHARS:
        t = t[:MAX_TTS_CHARS]
    t = re.sub(r"[*_#`]", "", t)
    return t


async def synthesize(text: str) -> tuple[bytes, str]:
    cleaned = _clean_text(text)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Leerer Text")

    provider = settings.tts_provider

    if provider == "gtts":
        return await _gtts(cleaned)
    if provider == "edge":
        try:
            return await _edge(cleaned)
        except HTTPException:
            return await _gtts(cleaned)
    if provider == "elevenlabs":
        return await _elevenlabs(cleaned)
    if provider == "piper":
        return await _piper(cleaned)
    if provider == "browser":
        raise HTTPException(
            status_code=400,
            detail="Server-TTS aus (browser). Frontend nutzt Web Speech API.",
        )

    raise HTTPException(status_code=400, detail=f"TTS_PROVIDER unbekannt: {provider}")


async def _gtts(text: str) -> tuple[bytes, str]:
    try:
        from gtts import gTTS
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="gTTS nicht installiert") from exc

    import asyncio

    def _sync() -> bytes:
        buf = io.BytesIO()
        gTTS(text=text, lang=settings.gtts_lang).write_to_fp(buf)
        return buf.getvalue()

    data = await asyncio.to_thread(_sync)
    if not data:
        raise HTTPException(status_code=502, detail="gTTS lieferte keine Audiodaten")
    return data, "audio/mpeg"


async def _edge(text: str) -> tuple[bytes, str]:
    try:
        import edge_tts
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="edge-tts nicht installiert") from exc

    voice = settings.edge_tts_voice or "de-DE-ConradNeural"
    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text, voice)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    data = buf.getvalue()
    if not data:
        raise HTTPException(status_code=502, detail="Edge TTS lieferte keine Audiodaten")
    return data, "audio/mpeg"


async def _piper(text: str) -> tuple[bytes, str]:
    url = (settings.piper_url or "").rstrip("/")
    if not url:
        raise HTTPException(status_code=503, detail="PIPER_URL nicht gesetzt")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{url}/",
                json={"text": text},
                headers={"Content-Type": "application/json"},
            )
            if r.status_code >= 400:
                r = await client.get(f"{url}", params={"text": text})
            r.raise_for_status()
            ctype = r.headers.get("content-type", "audio/wav")
            return r.content, ctype
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Piper Fehler: {exc}") from exc


async def _elevenlabs(text: str) -> tuple[bytes, str]:
    if not settings.elevenlabs_api_key:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY fehlt")
    voice = settings.elevenlabs_voice_id or "onwK4e9ZLuTAKqWW03F9"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": settings.elevenlabs_model,
        "language_code": "de",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.15,
            "use_speaker_boost": True,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.content, "audio/mpeg"
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ElevenLabs Fehler: {exc}") from exc


async def tts_response(text: str) -> Response:
    data, media = await synthesize(text)
    return Response(content=data, media_type=media)
