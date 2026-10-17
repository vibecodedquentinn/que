"""Steuerbefehle per Namens-/Raum-Matching — ohne kleines LLM."""

from __future__ import annotations

import re
import unicodedata

from app.response_style import control_reply, parse_json
from app.tools.registry import run_tool


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = t.replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("ß", "ss")
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _tokens(n: str) -> set[str]:
    return set(n.split())


def _detect_action(n: str) -> tuple[str, str | None] | None:
    """Returns (action, optional value for set)."""
    temp = re.search(r"(\d{1,2})\s*grad", n)
    if temp and re.search(r"\b(heiz|thermo|temperatur|warm|kalt)\b", n):
        return ("set", temp.group(1))

    bright = re.search(r"(\d{1,3})\s*(prozent|%|hell)", n)
    if bright and re.search(r"\b(licht|hell|dim|dunkel)\b", n):
        return ("set", bright.group(1))

    if re.search(r"\b(aus|ausmachen|abschalten|ausschalten|off|runter)\b", n):
        return ("off", None)
    if re.search(r"\b(an|ein|einschalten|anmachen|on|hoch)\b", n):
        return ("on", None)
    if re.search(r"\b(uml|toggle|wechsel)\b", n):
        return ("toggle", None)
    return None


def _is_control_utterance(n: str) -> bool:
    if _detect_action(n):
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


async def try_smart_home_control(user_text: str) -> str | None:
    raw = user_text.strip()
    if not raw:
        return None
    n = _norm(raw)
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
        (( _score_device(n, d), d) for d in devices),
        key=lambda x: x[0],
        reverse=True,
    )
    best_score, best = ranked[0]
    if best_score < 3:
        return None

    device_id = best.get("entity_id") or best.get("id")
    if not device_id:
        return None

    ctrl = await run_tool(
        "control_smart_device",
        {"device_id": device_id, "action": action, **({"value": value} if value else {})},
    )
    return control_reply(parse_json(ctrl))
