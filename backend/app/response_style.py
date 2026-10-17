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
        return f"Fritz!Box{_anrede_suffix()}: {data['error']}"
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
        return f"Gast-WLAN{_anrede_suffix()}: {data['error']}"
    state = "an" if data.get("enabled") else "aus"
    ssid = data.get("ssid") or "Gast-WLAN"
    return f"Gast-WLAN „{ssid}“ ist {state}{_anrede_suffix()}."


def reminder_added_reply(data: dict) -> str:
    if "error" in data:
        return f"Erinnerung nicht gespeichert{_anrede_suffix()}: {data['error']}"
    r = data.get("reminder", {})
    text = r.get("text", "")
    due = r.get("due_at") or ""
    extra = f" Termin: {due}." if due.strip() else ""
    return f"Notiert{_anrede_suffix()}: {text}.{extra}"


def reminders_list_reply(data: dict) -> str:
    items = data.get("reminders") or []
    if not items:
        return f"Keine offenen Erinnerungen{_anrede_suffix()}."
    lines = [f"• {r.get('text', '?')}" for r in items[:6]]
    more = len(items) - 6
    tail = f" … und {more} weitere." if more > 0 else ""
    return f"Offene Erinnerungen{_anrede_suffix()}: " + " ".join(lines) + tail


def note_saved_reply(data: dict) -> str:
    if "error" in data:
        return f"Notiz nicht gespeichert{_anrede_suffix()}: {data['error']}"
    note = data.get("note", {})
    title = note.get("title") or "Notiz"
    return f"Gespeichert{_anrede_suffix()}: {title}."


def notes_search_reply(data: dict) -> str:
    notes = data.get("notes") or []
    if not notes:
        return f"Dazu habe ich keine Notiz gefunden{_anrede_suffix()}."
    first = notes[0]
    body = (first.get("body") or "")[:120]
    return f"Gefunden{_anrede_suffix()}: {first.get('title', 'Notiz')} — {body}"


def identity_reply() -> str:
    return (
        f"Ich bin Jürgen — {settings.assistant_name}, {settings.assistant_acronym}. "
        f"Ihr Haus-Navigator: ruhig, präzise, mit trockenem Humor{_anrede_suffix()}. "
        "Fragen Sie nach Uhrzeit, Wetter, Geräten oder sagen Sie, was ich schalten soll."
    )


def format_tool_turn(tool_name: str, raw_result: str, *, guest_action: str = "") -> str | None:
    data = parse_json(raw_result)
    match tool_name:
        case "get_datetime":
            return time_reply(data)
        case "get_weather":
            return weather_reply(data, data.get("location", ""))
        case "list_smart_devices":
            return devices_reply(data)
        case "control_smart_device":
            return control_reply(data)
        case "fritz_list_hosts":
            return fritz_hosts_reply(data)
        case "fritz_internet_status":
            return fritz_wan_reply(data)
        case "fritz_guest_wifi":
            return fritz_guest_reply(data, guest_action or "on")
        case "add_reminder":
            return reminder_added_reply(data)
        case "list_reminders":
            return reminders_list_reply(data)
        case "save_note":
            return note_saved_reply(data)
        case "search_notes":
            return notes_search_reply(data)
        case _:
            return None


def parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": raw}
