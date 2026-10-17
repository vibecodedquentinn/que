from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

NOTES_FILE = Path(settings.data_dir) / "notes.json"


def _ensure() -> list[dict]:
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not NOTES_FILE.exists():
        NOTES_FILE.write_text("[]", encoding="utf-8")
    return json.loads(NOTES_FILE.read_text(encoding="utf-8"))


def _save(items: list[dict]) -> None:
    NOTES_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


async def save_note(title: str, body: str) -> str:
    items = _ensure()
    note = {
        "id": str(uuid.uuid4())[:8],
        "title": title or "Notiz",
        "body": body,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(note)
    _save(items)
    return json.dumps({"ok": True, "note": note}, ensure_ascii=False)


async def search_notes(query: str) -> str:
    q = query.lower()
    matches = [
        n
        for n in _ensure()
        if q in n.get("title", "").lower() or q in n.get("body", "").lower()
    ]
    return json.dumps({"notes": matches[:20]}, ensure_ascii=False)
