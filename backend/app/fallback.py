"""Offline/demo responses when no LLM API key is configured."""

from __future__ import annotations

import json
import re

from app.config import settings
from app.tools.registry import run_tool


def _tail() -> str:
    a = settings.address(leading_comma=True)
    return a if a else ""


async def fallback_reply(user_text: str) -> str:
    text = user_text.strip()
    lower = text.lower()
    tail = _tail()

    if re.search(r"\b(hallo|hi|hey|guten (tag|morgen|abend)|jürgen|juergen)\b", lower):
        return (
            f"Guten Tag{tail}. {settings.assistant_name} ist online. "
            f"Wobei darf ich unterstützen?"
        )

    if re.search(r"\b(uhrzeit|wie spät|datum)\b", lower):
        raw = await run_tool("get_datetime", {})
        data = json.loads(raw)
        return (
            f"Es ist {data.get('formatted', 'unbekannt')}{tail} "
            f"({data.get('timezone', 'Europe/Berlin')})."
        )

    weather_match = re.search(
        r"wetter\s+(?:in\s+)?([a-zäöüß\- ]+)", lower
    ) or re.search(r"weather\s+(?:in\s+)?([a-z\- ]+)", lower)
    if weather_match:
        loc = weather_match.group(1).strip().title()
        raw = await run_tool("get_weather", {"location": loc})
        w = json.loads(raw)
        if "error" in w:
            return f"{w['error']}{tail}."
        return (
            f"In {w.get('location', loc)} sind es {w.get('temperature_c')} Grad Celsius, "
            f"{w.get('description')}. Luftfeuchtigkeit {w.get('humidity_percent')} Prozent{tail}."
        )

    if re.search(r"\b(gerät|geräte|smart.?home|lichter)\b", lower):
        raw = await run_tool("list_smart_devices", {})
        return f"Aktueller Gerätestatus{tail}: {raw}"

    if "licht" in lower and "wohnzimmer" in lower:
        action = "on" if re.search(r"\b(an|ein)\b", lower) else "off"
        raw = await run_tool(
            "control_smart_device",
            {"device_id": "living_room_light", "action": action},
        )
        return f"Erledigt{tail}. {raw}"

    return (
        f"Entschuldigung{tail}. Für freie Konversation benötige ich einen "
        "LLM_API_KEY / LLM_BASE_URL (z. B. Ollama) in der `.env`. Bis dahin verstehe ich Uhrzeit, Wetter, "
        "Geräteliste und „Wohnzimmer Licht an/aus“."
    )
