from __future__ import annotations

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
    # Strip markdown-ish noise for speech
    t = re.sub(r"[*_#`]", "", t)
    return t


async def synthesize(text: str) -> tuple[bytes, str]:
    """Return (audio_bytes, media_type)."""
    cleaned = _clean_text(text)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Leerer Text")

    provider = settings.tts_provider

    if provider == "elevenlabs":
        return await _elevenlabs(cleaned)
    if provider == "piper":
        return await _piper(cleaned)

    raise HTTPException(
        status_code=400,
        detail="Server-TTS deaktiviert (TTS_PROVIDER=browser). Nutze Browser-Sprachausgabe.",
    )


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
                # Wyoming/openai-style piper HTTP servers vary — try query fallback
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
    voice = settings.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"
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
