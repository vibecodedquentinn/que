"""Steuerbefehle per Namens-/Raum-Matching — ohne kleines LLM."""

from __future__ import annotations

import re
import unicodedata

from app.response_style import control_reply, devices_reply, parse_json
from app.tools.registry import run_tool


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = t.replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("ß", "ss")
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _tokens(n: str) -> set[str]:
    return set(n.split())


def _detect_action(n: str) -> tuple[str, str | None] | None:
    temp = re.search(r"(\d{1,2})\s*grad", n)
    if temp and re.search(r"\b(heiz|thermo|temperatur|warm|kalt)\b", n):
        return ("set", temp.group(1))

    bright = re.search(r"(\d{1,3})\s*(prozent|%|hell)", n)
    if bright and re.search(r"\b(licht|hell|dim|dunkel)\b", n):
        return ("set", bright.group(1))

    if re.search(r"\b(aus|ausmachen|abschalten|ausschalten|off|runter|zu)\b", n):
        if re.search(r"\b(rollo|rollladen|jalousie)\b", n):
            return ("off", None)
        return ("off", None)
    if re.search(r"\b(an|ein|einschalten|anmachen|on|hoch|auf)\b", n):
        return ("on", None)
    if re.search(r"\b(uml|toggle|wechsel)\b", n):
        return ("toggle", None)
    return None


def _is_control_utterance(n: str) -> bool:
    if _detect_action(n):
        return True
    if re.search(r"\b(dunkel|heller|dimme)\b", n):
        return True
    return bool(
        re.search(
            r"\b(schalte|schalt|mach|mache|stell|stelle|dimme|fahr|heiz|klimatisier)\b",
            n,
        )
    )


def _score_device(n: str, device: dict) -> int:
    score = 0
    name = _norm(device.get("name", ""))
    room = _norm(device.get("room", ""))
    dtype = device.get("type", "")
    toks = _tokens(n)

    for part in name.split():
        if len(part) > 2 and part in toks:
            score += 4
    for part in room.split():
        if len(part) > 2 and part in toks:
            score += 3

    if "wohnzimmer" in n and "wohnzimmer" in room:
        score += 3
    if ("kuche" in n or "kueche" in n) and "kuche" in room:
        score += 3
    if "schlafzimmer" in n and "schlafzimmer" in room:
        score += 3
    if "flur" in n and "flur" in room:
        score += 3
    if ("arbeitszimmer" in n or "schreibtisch" in n) and (
        "arbeitszimmer" in room or "schreibtisch" in name
    ):
        score += 3

    if re.search(r"\b(licht|lampe|beleuchtung)\b", n) and dtype == "light":
        score += 2
    if re.search(r"\b(steckdose|stecker|plug)\b", n) and dtype == "switch":
        score += 2
    if re.search(r"\b(rollladen|rollo|jalousie|fenster)\b", n) and dtype == "cover":
        score += 2
    if re.search(r"\b(heiz|thermo|temperatur|grad)\b", n) and dtype == "climate":
        score += 2

    return score


async def try_all_lights(user_text: str) -> str | None:
    n = _norm(user_text)
    if not re.search(r"\b(alle|uberall|überall|komplett|everything)\b", n):
        return None
    if not re.search(r"\b(licht|lichter|lampen|beleuchtung)\b", n):
        return None
    action_pair = _detect_action(n) or ("off", None)
    action = action_pair[0]

    raw_json = await run_tool("list_smart_devices", {})
    data = parse_json(raw_json)
    lights = [d for d in data.get("devices") or [] if d.get("type") == "light"]
    if not lights:
        return None

    names: list[str] = []
    for d in lights:
        did = d.get("entity_id") or d.get("id")
        if not did:
            continue
        await run_tool(
            "control_smart_device",
            {"device_id": did, "action": action},
        )
        names.append(d.get("name", did))

    verb = "aus" if action == "off" else "an"
    return f"Erledigt. Alle Lichter ({len(names)}) sind {verb}."


async def try_smart_home_control(
    user_text: str,
    *,
    device_hint: str | None = None,
) -> str | None:
    raw = user_text.strip()
    if not raw:
        return None

    bulk = await try_all_lights(raw)
    if bulk:
        return bulk

    n = _norm(raw)
    if device_hint and _score_device(_norm(device_hint), {"name": device_hint, "room": device_hint, "type": "light"}) >= 0:
        n = f"{n} {_norm(device_hint)}"

    if not _is_control_utterance(n):
        return None

    action_pair = _detect_action(n)
    if not action_pair:
        if re.search(r"\b(schalte|mach|stell)\b", n):
            action_pair = ("toggle", None)
        else:
            return None

    action, value = action_pair

    raw_json = await run_tool("list_smart_devices", {})
    data = parse_json(raw_json)
    devices = data.get("devices") or []
    if not devices:
        return None

    ranked = sorted(
        ((_score_device(n, d), d) for d in devices),
        key=lambda x: x[0],
        reverse=True,
    )
    best_score, best = ranked[0]
    if best_score < 3 and not device_hint:
        return None

    if device_hint and best_score < 3:
        hint_n = _norm(device_hint)
        for d in devices:
            if hint_n in _norm(d.get("name", "")) or hint_n in _norm(d.get("room", "")):
                best = d
                break

    device_id = best.get("entity_id") or best.get("id")
    if not device_id:
        return None

    ctrl = await run_tool(
        "control_smart_device",
        {"device_id": device_id, "action": action, **({"value": value} if value else {})},
    )
    return control_reply(parse_json(ctrl))
