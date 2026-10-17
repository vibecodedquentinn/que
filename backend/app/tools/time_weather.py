from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx


async def get_datetime(timezone: str | None = None) -> str:
    tz_name = timezone or "Europe/Berlin"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return json.dumps(
            {"error": f"Unbekannte Zeitzone: {tz_name}"}, ensure_ascii=False
        )
    now = datetime.now(tz)
    weekdays = [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ]
    formatted = (
        f"{weekdays[now.weekday()]}, {now.day:02d}.{now.month:02d}.{now.year} "
        f"{now.hour:02d}:{now.minute:02d} Uhr"
    )
    return json.dumps(
        {
            "timezone": tz_name,
            "iso": now.isoformat(),
            "formatted": formatted,
        },
        ensure_ascii=False,
    )


async def get_weather(location: str) -> str:
    url = f"https://wttr.in/{location}?format=j1"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers={"User-Agent": "JUERGEN-Home/1.0"})
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return json.dumps(
            {"error": f"Wetter konnte nicht geladen werden: {exc}"},
            ensure_ascii=False,
        )

    current = data.get("current_condition", [{}])[0]
    area = data.get("nearest_area", [{}])[0]
    place = (area.get("areaName") or [{}])[0].get("value", location)
    temp = current.get("temp_C", "?")
    desc = (current.get("lang_de") or current.get("weatherDesc") or [{}])[0].get(
        "value", "—"
    )
    humidity = current.get("humidity", "?")
    wind = current.get("windspeedKmph", "?")

    return json.dumps(
        {
            "location": place,
            "temperature_c": temp,
            "description": desc,
            "humidity_percent": humidity,
            "wind_kmph": wind,
        },
        ensure_ascii=False,
    )
