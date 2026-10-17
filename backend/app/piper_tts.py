from __future__ import annotations

import asyncio
import io
import wave
from pathlib import Path

from fastapi import HTTPException

from app.config import settings

_voice = None
_lock = asyncio.Lock()


def _voice_dir() -> Path:
    return Path(settings.data_dir) / "voices"


def _model_paths() -> tuple[Path, Path]:
    name = settings.piper_voice
    d = _voice_dir()
    return d / f"{name}.onnx", d / f"{name}.onnx.json"


def _ensure_model() -> Path:
    onnx, _cfg = _model_paths()
    if onnx.is_file():
        return onnx
    try:
        from piper.download_voices import download_voice
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="piper-tts fehlt") from exc
    _voice_dir().mkdir(parents=True, exist_ok=True)
    download_voice(settings.piper_voice, _voice_dir())
    if not onnx.is_file():
        raise HTTPException(status_code=502, detail="Piper-Stimme konnte nicht geladen werden")
    return onnx


def _load_voice():
    global _voice
    if _voice is not None:
        return _voice
    from piper.voice import PiperVoice

    onnx = _ensure_model()
    _voice = PiperVoice.load(onnx)
    return _voice


def _synthesize_sync(text: str) -> bytes:
    voice = _load_voice()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        voice.synthesize_wav(text, wf)
    return buf.getvalue()


async def synthesize_piper_wav(text: str) -> tuple[bytes, str]:
    async with _lock:
        data = await asyncio.to_thread(_synthesize_sync, text)
    if not data:
        raise HTTPException(status_code=502, detail="Piper: leere Audiodatei")
    return data, "audio/wav"
