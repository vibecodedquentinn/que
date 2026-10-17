from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

REMINDERS_FILE = Path(settings.data_dir) / "reminders.json"


def _ensure() -> list[dict]:
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not REMINDERS_FILE.exists():
        REMINDERS_FILE.write_text("[]", encoding="utf-8")
    return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))


def _save(items: list[dict]) -> None:
    REMINDERS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def add_reminder(text: str, due_at: str | None = None) -> str:
    items = _ensure()
    item = {
        "id": str(uuid.uuid4())[:8],
        "text": text,
        "due_at": due_at or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "done": False,
    }
    items.append(item)
    _save(items)
    return json.dumps({"ok": True, "reminder": item}, ensure_ascii=False)


async def list_reminders() -> str:
    items = [r for r in _ensure() if not r.get("done")]
    return json.dumps({"reminders": items}, ensure_ascii=False)
