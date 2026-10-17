"""Natürliche Antworten im Jürgen-Stil — unabhängig vom LLM."""

from __future__ import annotations

import json
import random

from app.config import settings


def _du() -> str:
    t = settings.user_title.strip()
    return t if t else ""


def _anrede_suffix() -> str:
    t = _du()
    return f", {t}" if t else ""


_TIME_TAIL = [
    "Alles andere auf dem Plan?",
    "Was steht als Nächstes an?",
    "Soll ich noch etwas prüfen?",
]


def time_reply(data: dict) -> str:
    formatted = data.get("formatted", "unbekannt")
    tz = data.get("timezone", "Europe/Berlin")
    tail = random.choice(_TIME_TAIL)
    return f"{formatted}{_anrede_suffix()}. {tail}"


def weather_reply(data: dict, location: str) -> str:
    if "error" in data:
        return f"Das Wetter konnte ich leider nicht abrufen{_anrede_suffix()}: {data['error']}"
    loc = data.get("location", location)
    return (
        f"In {loc} sind es {data.get('temperature_c')} Grad, {data.get('description')}{_anrede_suffix()}. "
        f"Luftfeuchtigkeit {data.get('humidity_percent')} Prozent, Wind {data.get('wind_kmph')} km/h."
    )


def devices_reply(data: dict) -> str:
    devices = data.get("devices", [])
    if not devices:
        return f"Ich sehe gerade keine Geräte{_anrede_suffix()}."
    lines = []
    for d in devices[:8]:
        name = d.get("name", d.get("id"))
        state = d.get("state", "?")
        lines.append(f"{name}: {state}")
    more = len(devices) - 8
    extra = f" … und {more} weitere." if more > 0 else ""
    return (
        f"Ich habe {len(devices)} Geräte im Blick{_anrede_suffix()}: "
        + "; ".join(lines)
        + extra
    )


def control_reply(data: dict) -> str:
    if "error" in data:
        return f"Das hat nicht geklappt{_anrede_suffix()}: {data['error']}"
    dev = data.get("device", {})
    name = dev.get("name", "Gerät")
    state = dev.get("state", "ok")
    return f"Erledigt{_anrede_suffix()}. {name} ist jetzt {state}."


def fritz_hosts_reply(data: dict) -> str:
    if "error" in data:
        return f"Fritz!Box{ _anrede_suffix()}: {data['error']}"
    active = data.get("active_hosts") or []
    if not active:
        return f"Am Router sehe ich gerade keine aktiven Geräte{_anrede_suffix()}."
    names = [
        f"{h.get('name', '?')} ({h.get('ip', '?')})"
        for h in active[:10]
    ]
    extra = len(active) - 10
    tail = f" und {extra} weitere" if extra > 0 else ""
    return (
        f"Im Heimnetz sind {len(active)} Geräte aktiv{_anrede_suffix()}: "
        + ", ".join(names)
        + tail
        + "."
    )


def fritz_wan_reply(data: dict) -> str:
    if "error" in data:
        return f"Internetstatus nicht verfügbar{_anrede_suffix()}: {data['error']}"
    status = data.get("connection_status", "unbekannt")
    ip = data.get("external_ip", "—")
    return (
        f"Internet: {status}{_anrede_suffix()}. Externe IP: {ip}."
    )


def fritz_guest_reply(data: dict, action: str) -> str:
    if "error" in data:
        return f"Gast-WLAN{ _anrede_suffix()}: {data['error']}"
    state = "an" if data.get("enabled") else "aus"
    ssid = data.get("ssid") or "Gast-WLAN"
    return f"Gast-WLAN „{ssid}“ ist {state}{_anrede_suffix()}."


def identity_reply() -> str:
    return (
        f"Ich bin Jürgen — {settings.assistant_name}, {settings.assistant_acronym}. "
        f"Ihr Haus-Navigator: ruhig, präzise, mit trockenem Humor{_anrede_suffix()}. "
        "Fragen Sie nach Uhrzeit, Wetter, Geräten oder sagen Sie, was ich schalten soll."
    )


def parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": raw}
