from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

DEVICES_FILE = Path(settings.data_dir) / "devices.json"

DEFAULT_DEVICES = [
    {
        "id": "living_room_light",
        "name": "Wohnzimmer Licht",
        "type": "light",
        "room": "Wohnzimmer",
        "state": "off",
        "brightness": 70,
    },
    {
        "id": "kitchen_light",
        "name": "Küche Licht",
        "type": "light",
        "room": "Küche",
        "state": "on",
        "brightness": 100,
    },
    {
        "id": "desk_plug",
        "name": "Schreibtisch Steckdose",
        "type": "switch",
        "room": "Arbeitszimmer",
        "state": "on",
    },
    {
        "id": "bedroom_blinds",
        "name": "Schlafzimmer Rollladen",
        "type": "cover",
        "room": "Schlafzimmer",
        "state": "closed",
        "position": 0,
    },
    {
        "id": "thermostat_hall",
        "name": "Flur Thermostat",
        "type": "climate",
        "room": "Flur",
        "state": "on",
        "temperature": 21.0,
        "target": 21.0,
    },
]


def _ensure_file() -> None:
    DEVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DEVICES_FILE.exists():
        DEVICES_FILE.write_text(
            json.dumps(DEFAULT_DEVICES, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _load() -> list[dict]:
    _ensure_file()
    return json.loads(DEVICES_FILE.read_text(encoding="utf-8"))


def _save(devices: list[dict]) -> None:
    DEVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEVICES_FILE.write_text(
        json.dumps(devices, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def list_devices() -> str:
    return json.dumps({"devices": _load()}, ensure_ascii=False)


async def control_device(device_id: str, action: str, value: str | None = None) -> str:
    devices = _load()
    device = next((d for d in devices if d["id"] == device_id), None)
    if not device:
        return json.dumps(
            {"error": f"Gerät nicht gefunden: {device_id}"}, ensure_ascii=False
        )

    dtype = device.get("type", "switch")

    if action == "toggle":
        if dtype in ("light", "switch", "climate"):
            device["state"] = "off" if device.get("state") == "on" else "on"
        elif dtype == "cover":
            device["state"] = "closed" if device.get("state") == "open" else "open"
            device["position"] = 0 if device.get("state") == "closed" else 100
    elif action == "on":
        device["state"] = "on"
        if dtype == "cover":
            device["state"] = "open"
            device["position"] = 100
    elif action == "off":
        device["state"] = "off"
        if dtype == "cover":
            device["state"] = "closed"
            device["position"] = 0
    elif action == "set" and value is not None:
        if dtype == "climate":
            try:
                target = float(value.replace(",", ".").split()[0])
                device["target"] = target
                device["state"] = "on"
            except ValueError:
                return json.dumps({"error": "Ungültige Temperatur"}, ensure_ascii=False)
        elif dtype == "light":
            try:
                device["brightness"] = max(0, min(100, int(value.split()[0])))
                device["state"] = "on" if device["brightness"] > 0 else "off"
            except ValueError:
                return json.dumps(
                    {"error": "Ungültige Helligkeit"}, ensure_ascii=False
                )
        else:
            return json.dumps(
                {"error": f"Set nicht unterstützt für {dtype}"}, ensure_ascii=False
            )
    else:
        return json.dumps({"error": f"Unbekannte Aktion: {action}"}, ensure_ascii=False)

    _save(devices)
    return json.dumps({"ok": True, "device": device}, ensure_ascii=False)
