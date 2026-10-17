"""Erkennt Standardbefehle und antwortet zuverlässig — ohne kleines LLM."""

from __future__ import annotations

import re
import unicodedata

from app.integrations import fritzbox as fb
from app.response_style import (
    devices_reply,
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
from app.session_context import get_ctx, set_ctx
from app.smart_home_intent import try_smart_home_control
from app.social_replies import try_social_reply
from app.tools.registry import run_tool


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = t.replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("ß", "ss")
    return t


async def _remember(session_id: str, reply: str, **ctx: str) -> str:
    await set_ctx(session_id, "last_reply", reply)
    for k, v in ctx.items():
        if v:
            await set_ctx(session_id, k, v)
    return reply


async def route_intent(session_id: str, user_text: str) -> str | None:
    raw = user_text.strip()
    if not raw:
        return None
    n = _norm(raw)

    social = try_social_reply(raw)
    if social:
        return await _remember(session_id, social)

    if re.search(r"\b(nochmal|wiederhol|repeat|noch mal)\b", n):
        prev = await get_ctx(session_id, "last_reply")
        if prev:
            return prev

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
        reply = reminder_added_reply(parse_json(raw_json))
        return await _remember(session_id, reply)

    if re.search(
        r"\b(wie spat|wie spät|wie spaet|uhrzeit|uhr|welche zeit|wie viel uhr|"
        r"wie late|datum|welcher tag|tag ist heute|clock|time|wie spat ist|"
        r"sag mir die zeit|aktuelle zeit|wie spät haben wir|wie viel uhr ist)\b",
        n,
    ) or n in {"spat", "wie spat"} or re.fullmatch(r"zeit\??", n):
        raw_json = await run_tool("get_datetime", {})
        reply = time_reply(parse_json(raw_json))
        return await _remember(session_id, reply)

    from app.smart_home_intent import try_all_lights

    bulk = await try_all_lights(raw)
    if bulk:
        return await _remember(session_id, bulk)

    device_hint = await get_ctx(session_id, "last_device_name")
    if re.search(r"\b(da|dort|das|nochmal|gleiche)\b", n) and len(n.split()) <= 5:
        smart = await try_smart_home_control(raw, device_hint=device_hint)
    else:
        smart = await try_smart_home_control(raw)
    if smart:
        m = re.search(r"\. (.+?) ist jetzt", smart)
        hint = m.group(1) if m else ""
        return await _remember(session_id, smart, last_device_name=hint)

    # Follow-up Wetter: „Und in Hamburg?“ / „Was ist mit München?“
    city_fu = re.search(r"^(?:und\s+)?in\s+([a-z\- ]{2,})\s*\??$", n) or re.search(
        r"^was ist mit\s+([a-z\- ]{2,})\s*\??$", n
    )
    if city_fu:
        loc = city_fu.group(1).strip().title()
        raw_json = await run_tool("get_weather", {"location": loc})
        reply = weather_reply(parse_json(raw_json), loc)
        return await _remember(session_id, reply, last_weather_city=loc)

    last_city = await get_ctx(session_id, "last_weather_city")
    if last_city and re.search(r"\b(dort|da|gleiche stadt|nochmal wetter)\b", n):
        raw_json = await run_tool("get_weather", {"location": last_city})
        reply = weather_reply(parse_json(raw_json), last_city)
        return await _remember(session_id, reply, last_weather_city=last_city)

    if (
        re.search(r"\bwetter\b", n)
        or re.search(r"\bweather\b", n)
        or re.search(r"\b(regnet|regen|schirm|jacke|warm|kalt|grad draussen)\b", n)
    ):
        loc = last_city or "Berlin"
        weather_match = re.search(
            r"wetter\s+(?:in\s+|fuer\s+|für\s+)?([a-z\- ]+)", n
        ) or re.search(r"weather\s+(?:in\s+)?([a-z\- ]+)", n)
        if weather_match:
            loc = weather_match.group(1).strip().title() or loc
        raw_json = await run_tool("get_weather", {"location": loc})
        reply = weather_reply(parse_json(raw_json), loc)
        return await _remember(session_id, reply, last_weather_city=loc)

    if re.search(
        r"\b(geräte|gerate|smart.?home|alle licht|liste.*gerat|was ist an|"
        r"was ist aus|welche geraete|zeig.*gerat|status.*gerat|ubersicht)\b",
        n,
    ):
        raw_json = await run_tool("list_smart_devices", {})
        reply = devices_reply(parse_json(raw_json))
        return await _remember(session_id, reply)

    if re.search(
        r"\b(wer bist du|was bist du|dein name|wie heisst du|wie heißt du|stell dich vor|"
        r"was kannst du|was kannst|wer spricht)\b",
        n,
    ):
        reply = identity_reply()
        return await _remember(session_id, reply)

    if re.search(r"\b(erinnerungen|offene erinnerung|was steht an)\b", n):
        raw_json = await run_tool("list_reminders", {})
        reply = reminders_list_reply(parse_json(raw_json))
        return await _remember(session_id, reply)

    if re.search(r"\b(notier|schreib.*auf|merk dir|save note)\b", n):
        body = re.sub(
            r"^(notier(?:e)?|schreib(?:e)? (?:mir )?auf|merk dir)\s*",
            "",
            raw,
            flags=re.I,
        ).strip()
        if body:
            raw_json = await run_tool("save_note", {"title": "Sprachnotiz", "body": body})
            reply = note_saved_reply(parse_json(raw_json))
            return await _remember(session_id, reply)

    if fb.configured() and re.search(r"\bfritz", n):
        if re.search(
            r"\b(wer ist im wlan|verbundene gerate|fritzbox gerate|heimnetz geraete)\b",
            n,
        ):
            raw_json = await run_tool("fritz_list_hosts", {})
            reply = fritz_hosts_reply(parse_json(raw_json))
            return await _remember(session_id, reply)
        if re.search(r"\b(gast.?wlan|guest wifi)\b", n):
            action = "on" if re.search(r"\b(an|ein|einschalten)\b", n) else "off"
            raw_json = await run_tool("fritz_guest_wifi", {"action": action})
            reply = fritz_guest_reply(parse_json(raw_json), action)
            return await _remember(session_id, reply)

    return None
