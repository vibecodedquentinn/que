"""Kurzzeit-Kontext pro Session (Follow-ups ohne großes LLM)."""

from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

from app.config import settings

DB_PATH = Path(settings.data_dir) / "juergen.db"


async def _ensure_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS session_context (
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (session_id, key)
            )
            """
        )
        await db.commit()


async def get_ctx(session_id: str, key: str) -> str | None:
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT value FROM session_context WHERE session_id = ? AND key = ?",
            (session_id, key),
        )
        row = await cur.fetchone()
    return row[0] if row else None


async def set_ctx(session_id: str, key: str, value: str) -> None:
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO session_context (session_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id, key) DO UPDATE SET
                value = excluded.value,
                updated_at = datetime('now')
            """,
            (session_id, key, value),
        )
        await db.commit()


async def get_all_ctx(session_id: str) -> dict[str, str]:
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT key, value FROM session_context WHERE session_id = ?",
            (session_id,),
        )
        rows = await cur.fetchall()
    return {k: v for k, v in rows}
