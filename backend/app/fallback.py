"""Antworten wenn kein LLM erreichbar — nutzt denselben Intent-Router."""

from __future__ import annotations

from app.config import settings
from app.intent_router import route_intent


async def fallback_reply(session_id: str, user_text: str) -> str:
    routed = await route_intent(session_id, user_text)
    if routed:
        return routed

    tail = settings.address(leading_comma=True)
    return (
        f"Ich habe Sie verstanden{tail}, aber für freie Gespräche braucht der Cloud-Server "
        "noch einen KI-Schlüssel (OpenRouter — einmal im Hosting eintragen). "
        "Uhrzeit, Wetter, Geräte, Erinnerungen und Schaltbefehle gehen trotzdem."
    )
