from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import settings


def configured() -> bool:
    return bool(
        settings.fritzbox_enabled
        and settings.fritzbox_host
        and settings.fritzbox_password
    )


@lru_cache(maxsize=1)
def _connection():
    from fritzconnection import FritzConnection

    return FritzConnection(
        address=settings.fritzbox_host,
        user=settings.fritzbox_user or "",
        password=settings.fritzbox_password,
        timeout=10,
    )


async def ping() -> bool:
    if not configured():
        return False
    try:
        fc = _connection()
        return bool(fc.call_action("DeviceInfo:1", "GetInfo"))
    except Exception:
        _connection.cache_clear()
        return False


def _hosts() -> list[dict[str, Any]]:
    from fritzconnection.lib.fritzhosts import FritzHosts

    fc = _connection()
    fh = FritzHosts(fc=fc)
    out: list[dict[str, Any]] = []
    for h in fh.get_hosts_info() or []:
        out.append(
            {
                "name": h.get("name") or "Unbekannt",
                "ip": h.get("ip") or "",
                "mac": h.get("mac") or "",
                "active": bool(h.get("status")),
            }
        )
    return out


async def list_hosts() -> str:
    if not configured():
        return json.dumps(
            {"error": "Fritz!Box nicht konfiguriert (FRITZBOX_* in .env)"},
            ensure_ascii=False,
        )
    try:
        hosts = _hosts()
        active = [h for h in hosts if h["active"]]
        return json.dumps(
            {
                "total": len(hosts),
                "active_count": len(active),
                "hosts": hosts,
                "active_hosts": active,
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        _connection.cache_clear()
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


async def internet_status() -> str:
    if not configured():
        return json.dumps({"error": "Fritz!Box nicht konfiguriert"}, ensure_ascii=False)
    try:
        fc = _connection()
        status = fc.call_action("WANCommonInterfaceConfig:1", "GetStatusInfo")
        ext = fc.call_action("WANIPConnection:1", "GetStatusInfo")
        return json.dumps(
            {
                "connection_status": status.get("NewConnectionStatus"),
                "uptime_seconds": status.get("NewUptime"),
                "external_ip": ext.get("NewExternalIPAddress"),
                "uptime_ip_seconds": ext.get("NewUptime"),
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        _connection.cache_clear()
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


async def guest_wifi(action: str) -> str:
    if not configured():
        return json.dumps({"error": "Fritz!Box nicht konfiguriert"}, ensure_ascii=False)
    enable = 1 if action in ("on", "enable", "ein", "an") else 0
    try:
        fc = _connection()
        # Gast-WLAN ist auf vielen Boxen WLANConfiguration:2 oder :3
        last_error = None
        for sid in ("WLANConfiguration:2", "WLANConfiguration:3", "WLANConfiguration:4"):
            try:
                fc.call_action(sid, "SetEnable", NewEnable=enable)
                info = fc.call_action(sid, "GetInfo")
                return json.dumps(
                    {
                        "ok": True,
                        "service": sid,
                        "enabled": bool(info.get("NewEnable")),
                        "ssid": info.get("NewSSID"),
                    },
                    ensure_ascii=False,
                )
            except Exception as exc:
                last_error = exc
                continue
        return json.dumps(
            {"error": f"Gast-WLAN nicht gefunden: {last_error}"},
            ensure_ascii=False,
        )
    except Exception as exc:
        _connection.cache_clear()
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
