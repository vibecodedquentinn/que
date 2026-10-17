"""Schnelle, zuverlässige Antworten ohne LLM (Begrüßung, Name)."""

from __future__ import annotations

import re
import unicodedata

from app.config import settings


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = t.replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("ß", "ss")
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _address_prefix() -> str:
    if settings.user_title.strip():
        return f"Hallo, {settings.user_title.strip()}."
    return "Hallo."


async def try_quick_reply(user_text: str) -> str | None:
    raw = user_text.strip()
    if not raw:
        return None

    n = _norm(raw)
    words = n.split()

    greeting_words = {"hallo", "hey", "hi", "moin", "servus", "gruezi", "grüezi"}
    time_greet = {"guten", "tag", "morgen", "abend", "nacht"}
    name_tokens = {"jurgen", "juergen", "jürgen"}

    has_name = any(w in name_tokens for w in words) or "jurgen" in n
    has_greeting = any(w in greeting_words for w in words) or (
        "guten" in words and any(w in time_greet for w in words)
    )

    # „Jürgen“, „Hallo Jürgen“, „Hey Jürgen“, nur Begrüßung
    if has_name and (has_greeting or len(words) <= 2):
        return (
            f"{_address_prefix()} Hier ist Jürgen, {settings.assistant_name}. "
            "Systeme sind online. Wobei darf ich helfen?"
        )

    if n in name_tokens or (len(words) == 1 and words[0] in name_tokens):
        return (
            f"{_address_prefix()} Ja, ich höre Sie. "
            "Sagen Sie mir, was ich steuern oder nachschauen soll."
        )

    if has_greeting and len(words) <= 4 and not re.search(r"\b(wetter|licht|uhr|gerat)\b", n):
        return (
            f"{_address_prefix()} Jürgen ist bereit. "
            "Fragen Sie nach Uhrzeit, Wetter, Geräten oder geben Sie einen Befehl."
        )

    if re.search(r"\b(wer bist du|wie heisst du|wie heißt du|dein name)\b", n):
        return (
            f"Ich bin Jürgen, {settings.assistant_name} — "
            f"{settings.assistant_acronym}. "
            "Ich unterstütze Sie im Smart Home und bei Alltagsfragen."
        )

    return None
