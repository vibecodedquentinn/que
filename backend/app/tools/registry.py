from __future__ import annotations

import json
from typing import Any

from app.tools import devices, notes, reminders, time_weather

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Aktuelle Uhrzeit und Datum für eine Zeitzone abfragen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA-Zeitzone, z.B. Europe/Berlin",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Wetter für einen Ort abfragen (Stadt oder Koordinaten-Text).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Stadtname, z.B. Berlin",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_smart_devices",
            "description": "Alle Smart-Home-Geräte und deren Status auflisten.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_smart_device",
            "description": "Ein Smart-Home-Gerät steuern (Licht, Steckdose, Thermostat, Rollladen).",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "Geräte-ID"},
                    "action": {
                        "type": "string",
                        "enum": ["on", "off", "toggle", "set"],
                        "description": "Aktion",
                    },
                    "value": {
                        "type": "string",
                        "description": "Optionaler Wert bei set (z.B. Temperatur 21, Helligkeit 80)",
                    },
                },
                "required": ["device_id", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": "Eine Erinnerung speichern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "due_at": {
                        "type": "string",
                        "description": "ISO-8601 oder natürliche Beschreibung (wird als Text gespeichert)",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_reminders",
            "description": "Offene Erinnerungen auflisten.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Eine Notiz für später speichern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Notizen nach Stichwort durchsuchen.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]


async def run_tool(name: str, arguments: str | dict[str, Any]) -> str:
    args: dict[str, Any]
    if isinstance(arguments, str):
        args = json.loads(arguments) if arguments.strip() else {}
    else:
        args = arguments

    match name:
        case "get_datetime":
            return await time_weather.get_datetime(args.get("timezone"))
        case "get_weather":
            return await time_weather.get_weather(args["location"])
        case "list_smart_devices":
            return await devices.list_devices()
        case "control_smart_device":
            return await devices.control_device(
                args["device_id"], args["action"], args.get("value")
            )
        case "add_reminder":
            return await reminders.add_reminder(args["text"], args.get("due_at"))
        case "list_reminders":
            return await reminders.list_reminders()
        case "save_note":
            return await notes.save_note(args.get("title", ""), args["body"])
        case "search_notes":
            return await notes.search_notes(args["query"])
        case _:
            return json.dumps({"error": f"Unbekanntes Tool: {name}"}, ensure_ascii=False)
