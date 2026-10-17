"""Erkennt Standardbefehle und antwortet zuverlässig — ohne kleines LLM."""

from __future__ import annotations

import re
import unicodedata

from app.integrations import fritzbox as fb
from app.response_style import (
    identity_reply,
    note_saved_reply,
    parse_json,
    reminder_added_reply,
    reminders_list_reply,
    time_reply,
    weather_reply,
    fritz_guest_reply,
    fritz_hosts_reply,
    fritz_wan_reply,
)
from app.smart_home_intent import try_smart_home_control
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
        r"wie late|datum|welcher tag|tag ist heute|clock|time|wie spat ist|"
        r"sag mir die zeit|aktuelle zeit)\b",
        n,
    ) or n in {"spat", "wie spat"} or re.fullmatch(r"zeit\??", n):
        raw_json = await run_tool("get_datetime", {})
        return time_reply(parse_json(raw_json))

    if re.search(r"\bwetter\b", n) or re.search(r"\bweather\b", n):
        loc = "Berlin"
        weather_match = re.search(
            r"wetter\s+(?:in\s+|fuer\s+|für\s+|für\s+)?([a-z\- ]+)", n
        ) or re.search(r"weather\s+(?:in\s+)?([a-z\- ]+)", n)
        if weather_match:
            loc = weather_match.group(1).strip().title() or loc
        raw_json = await run_tool("get_weather", {"location": loc})
        return weather_reply(parse_json(raw_json), loc)

    if re.search(
        r"\b(geräte|gerate|smart.?home|alle licht|liste.*gerat|was ist an|"
        r"was ist aus|welche geraete|zeig.*gerat|status.*gerat)\b",
        n,
    ):
        from app.response_style import devices_reply

        raw_json = await run_tool("list_smart_devices", {})
        return devices_reply(parse_json(raw_json))

    smart = await try_smart_home_control(raw)
    if smart:
        return smart

    if re.search(
        r"\b(wer bist du|was bist du|dein name|wie heisst du|wie heißt du|stell dich vor|"
        r"was kannst du|was kannst)\b",
        n,
    ):
        return identity_reply()

    if re.search(r"\b(erinnerungen|offene erinnerung|was steht an)\b", n):
        raw_json = await run_tool("list_reminders", {})
        return reminders_list_reply(parse_json(raw_json))

    remind = re.search(
        r"(?:erinner(?:e)? mich(?: daran)?(?:,?)?|remind me)\s+(?:an\s+|dass\s+)?(.+)",
        raw,
        re.I,
    )
    if remind:
        text = remind.group(1).strip().rstrip(".")
        due = None
        due_m = re.search(r"\b(um|am|morgen|heute abend)\s+(.+)$", text, re.I)
        if due_m:
            due = due_m.group(0)
            text = text[: due_m.start()].strip()
        raw_json = await run_tool(
            "add_reminder", {"text": text or raw, "due_at": due or ""}
        )
        return reminder_added_reply(parse_json(raw_json))

    if re.search(r"\b(notier|schreib.*auf|merk dir|save note)\b", n):
        body = re.sub(
            r"^(notier(?:e)?|schreib(?:e)? (?:mir )?auf|merk dir)\s*",
            "",
            raw,
            flags=re.I,
        ).strip()
        if body:
            raw_json = await run_tool("save_note", {"title": "Sprachnotiz", "body": body})
            return note_saved_reply(parse_json(raw_json))

    if re.search(r"\b(fritz|wlan|router|heimnetz|internet|gast.?wlan)\b", n):
        if re.search(
            r"\b(wer ist im wlan|wer ist online|verbundene geräte|verbundene gerate|"
            r"geräte am router|gerate am router|fritzbox geräte|heimnetz|wlan geraete)\b",
            n,
        ):
            raw_json = await run_tool("fritz_list_hosts", {})
            return fritz_hosts_reply(parse_json(raw_json))

        if re.search(
            r"\b(internet|wan|online|verbindung|geht das netz|externe ip|fritzbox status|"
            r"netzwerk status)\b",
            n,
        ):
            raw_json = await run_tool("fritz_internet_status", {})
            return fritz_wan_reply(parse_json(raw_json))

        if re.search(r"\b(gast.?wlan|gastwifi|guest wifi)\b", n):
            action = "on" if re.search(r"\b(an|ein|einschalten)\b", n) else "off"
            raw_json = await run_tool("fritz_guest_wifi", {"action": action})
            return fritz_guest_reply(parse_json(raw_json), action)

        if not fb.configured() and re.search(r"\bfritz", n):
            return (
                "Fritz!Box ist noch nicht angebunden — FRITZBOX_* in der Konfiguration setzen."
            )

    return None
