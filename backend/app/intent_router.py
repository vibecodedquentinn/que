"""Erkennt Standardbefehle und antwortet zuverlässig — ohne kleines LLM."""

from __future__ import annotations

import re
import unicodedata

from app.response_style import (
    control_reply,
    devices_reply,
    identity_reply,
    parse_json,
    time_reply,
    weather_reply,
)
from app.tools.registry import run_tool


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = t.replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("ß", "ss")
    return t


async def route_intent(user_text: str) -> str | None:
    raw = user_text.strip()
    if not raw:
        return None
    n = _norm(raw)

    if re.search(
        r"\b(wie spat|wie spät|wie spaet|uhrzeit|uhr|welche zeit|wie viel uhr|"
        r"wie late|datum|welcher tag|tag ist heute|clock|time)\b",
        n,
    ) or "spat" in n.split():
        raw_json = await run_tool("get_datetime", {})
        return time_reply(parse_json(raw_json))

    weather_match = re.search(
        r"wetter\s+(?:in\s+|fuer\s+|für\s+)?([a-z\- ]+)", n
    ) or re.search(r"weather\s+(?:in\s+)?([a-z\- ]+)", n)
    if re.search(r"\bwetter\b", n):
        loc = "Berlin"
        if weather_match:
            loc = weather_match.group(1).strip().title() or loc
        raw_json = await run_tool("get_weather", {"location": loc})
        return weather_reply(parse_json(raw_json), loc)

    if re.search(r"\b(geräte|gerate|smart.?home|alle licht|liste.*gerat|was ist an|was ist aus)\b", n):
        raw_json = await run_tool("list_smart_devices", {})
        return devices_reply(parse_json(raw_json))

    if "licht" in n and "wohnzimmer" in n:
        action = "on" if re.search(r"\b(an|ein|einschalten)\b", n) else "off"
        raw_json = await run_tool(
            "control_smart_device",
            {"device_id": "living_room_light", "action": action},
        )
        return control_reply(parse_json(raw_json))

    if re.search(r"\b(wer bist du|was bist du|dein name|wie heisst du|wie heißt du|stell dich vor)\b", n):
        return identity_reply()

    return None
