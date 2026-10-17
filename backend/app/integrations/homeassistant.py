from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings

DOMAINS = {"light", "switch", "cover", "climate", "fan", "media_player", "input_boolean"}


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.homeassistant_token}",
        "Content-Type": "application/json",
    }


def _base() -> str:
    return (settings.homeassistant_url or "").rstrip("/")


def configured() -> bool:
    return bool(settings.homeassistant_url and settings.homeassistant_token)


async def ping() -> bool:
    if not configured():
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{_base()}/api/", headers=_headers())
            return r.status_code == 200
    except Exception:
        return False


def _map_state(state: dict[str, Any]) -> dict[str, Any]:
    entity_id: str = state["entity_id"]
    domain = entity_id.split(".")[0]
    attrs = state.get("attributes") or {}
    raw = state.get("state", "unknown")
    on = raw in ("on", "open", "playing", "home")
    device: dict[str, Any] = {
        "id": entity_id,
        "entity_id": entity_id,
        "name": attrs.get("friendly_name") or entity_id,
        "type": domain if domain in DOMAINS else "switch",
        "room": attrs.get("area_id") or attrs.get("device_class") or "Home Assistant",
        "state": "on" if on else "off",
        "source": "homeassistant",
    }
    if domain == "light":
        br = attrs.get("brightness")
        if br is not None:
            device["brightness"] = max(0, min(100, int(round(br / 255 * 100))))
        device["state"] = "on" if raw == "on" else "off"
    elif domain == "cover":
        device["state"] = raw
        device["position"] = attrs.get("current_position")
    elif domain == "climate":
        device["temperature"] = attrs.get("current_temperature")
        device["target"] = attrs.get("temperature")
        device["state"] = "off" if raw == "off" else "on"
    return device


async def list_devices() -> str:
    if not configured():
        return json.dumps({"error": "Home Assistant nicht konfiguriert"}, ensure_ascii=False)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{_base()}/api/states", headers=_headers())
            r.raise_for_status()
            states = r.json()
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    devices = [
        _map_state(s)
        for s in states
        if s.get("entity_id", "").split(".")[0] in DOMAINS
    ]
    devices.sort(key=lambda d: d["name"].lower())
    return json.dumps({"devices": devices}, ensure_ascii=False)


async def _call_service(domain: str, service: str, entity_id: str, data: dict | None = None) -> None:
    payload: dict[str, Any] = {"entity_id": entity_id}
    if data:
        payload.update(data)
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{_base()}/api/services/{domain}/{service}",
            headers=_headers(),
            json=payload,
        )
        r.raise_for_status()


async def control_device(device_id: str, action: str, value: str | None = None) -> str:
    if not configured():
        return json.dumps({"error": "Home Assistant nicht konfiguriert"}, ensure_ascii=False)

    entity_id = device_id
    domain = entity_id.split(".")[0]
    try:
        if action == "toggle":
            await _call_service(domain, "toggle", entity_id)
        elif action == "on":
            await _call_service(domain, "turn_on", entity_id)
        elif action == "off":
            await _call_service(domain, "turn_off", entity_id)
        elif action == "set" and value is not None:
            if domain == "climate":
                temp = float(value.replace(",", ".").split()[0])
                await _call_service(domain, "set_temperature", entity_id, {"temperature": temp})
            elif domain == "light":
                pct = int(value.split()[0])
                await _call_service(
                    domain,
                    "turn_on",
                    entity_id,
                    {"brightness_pct": max(0, min(100, pct))},
                )
            elif domain == "cover":
                pos = int(value.split()[0])
                await _call_service(domain, "set_cover_position", entity_id, {"position": pos})
            else:
                return json.dumps(
                    {"error": f"Set nicht unterfützt für {domain}"}, ensure_ascii=False
                )
        else:
            return json.dumps({"error": f"Unbekannte Aktion: {action}"}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    # Refresh entity state
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{_base()}/api/states/{entity_id}", headers=_headers())
            r.raise_for_status()
            device = _map_state(r.json())
    except Exception:
        device = {"id": entity_id, "state": action}

    return json.dumps({"ok": True, "device": device}, ensure_ascii=False)
