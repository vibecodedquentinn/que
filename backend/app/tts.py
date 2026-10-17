from __future__ import annotations

import asyncio
import io
import re
import tempfile
from pathlib import Path

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
    chain = {
        "espeak": [_espeak, _gtts],
        "edge": [_edge, _espeak, _gtts],
        "gtts": [_gtts, _espeak],
        "elevenlabs": [_elevenlabs, _espeak],
        "piper": [_piper, _espeak],
        "browser": [],
    }.get(provider, [_espeak, _gtts])

    errors: list[str] = []
    for fn in chain:
        try:
            return await fn(cleaned)
        except HTTPException as exc:
            errors.append(str(exc.detail))
        except Exception as exc:
            errors.append(str(exc))

    raise HTTPException(status_code=502, detail=f"TTS fehlgeschlagen: {'; '.join(errors)}")


async def _espeak(text: str) -> tuple[bytes, str]:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        proc = await asyncio.create_subprocess_exec(
            "espeak-ng",
            "-v",
            settings.espeak_voice,
            "-s",
            str(settings.espeak_speed),
            "-p",
            str(settings.espeak_pitch),
            "-w",
            str(out),
            text,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            raise HTTPException(
                status_code=502,
                detail=f"espeak-ng: {(err or b'').decode()[:200]}",
            )
        data = out.read_bytes()
        if not data:
            raise HTTPException(status_code=502, detail="espeak-ng: leere Datei")
        return data, "audio/wav"
    finally:
        out.unlink(missing_ok=True)


async def _gtts(text: str) -> tuple[bytes, str]:
    try:
        from gtts import gTTS
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="gTTS nicht installiert") from exc

    def _sync() -> bytes:
        buf = io.BytesIO()
        gTTS(text=text, lang=settings.gtts_lang).write_to_fp(buf)
        return buf.getvalue()

    data = await asyncio.to_thread(_sync)
    if not data:
        raise HTTPException(status_code=502, detail="gTTS leer")
    return data, "audio/mpeg"


async def _edge(text: str) -> tuple[bytes, str]:
    try:
        import edge_tts
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="edge-tts fehlt") from exc

    voice = settings.edge_tts_voice or "de-DE-ConradNeural"
    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text, voice)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    data = buf.getvalue()
    if not data:
        raise HTTPException(status_code=502, detail="Edge TTS leer")
    return data, "audio/mpeg"


async def _piper(text: str) -> tuple[bytes, str]:
    url = (settings.piper_url or "").rstrip("/")
    if not url:
        raise HTTPException(status_code=503, detail="PIPER_URL fehlt")
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{url}/", json={"text": text})
        if r.status_code >= 400:
            r = await client.get(url, params={"text": text})
        r.raise_for_status()
        return r.content, r.headers.get("content-type", "audio/wav")


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
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.content, "audio/mpeg"


async def tts_response(text: str) -> Response:
    data, media = await synthesize(text)
    return Response(content=data, media_type=media)
