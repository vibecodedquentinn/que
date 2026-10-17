"""Kurze Jürgen-Antworten ohne LLM."""

from __future__ import annotations

import random
import re
import unicodedata

from app.config import settings


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = t.replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("ß", "ss")
    return re.sub(r"\s+", " ", t)


def _suffix() -> str:
    t = settings.user_title.strip()
    return f", {t}" if t else ""


def try_social_reply(user_text: str) -> str | None:
    n = _norm(user_text)
    if not n:
        return None

    if re.search(r"\b(danke|thanks|merci|dankeschon|dankeschoen)\b", n):
        opts = [
            f"Gern geschehen{_suffix()}.",
            f"Immer zu Diensten{_suffix()} — was als Nächstes?",
            f"Kein Problem{_suffix()}. Ich bin noch da.",
        ]
        return random.choice(opts)

    if re.search(r"\b(tschuss|tschüss|ciao|bye|bis spater|bis später|machs gut)\b", n):
        return f"Bis bald{_suffix()}. Ich halte die Leitung warm."

    if re.search(r"\b(okay|ok|alles klar|verstanden|passt|prima|super)\b", n) and len(n.split()) <= 4:
        return f"Alles klar{_suffix()}."

    if re.search(r"\b(witz|lacher|langweilig|witz erzähl)\b", n):
        opts = [
            f"Mein Humor ist trocken wie Heizungsluft{_suffix()} — dafür funktioniert die Heizung.",
            f"Ich bin kein Comedian{_suffix()}, eher der Typ, der die Uhrzeit korrekt hat.",
        ]
        return random.choice(opts)

    if re.search(r"\b(hilfe|help|was geht|commands|befehle)\b", n):
        return (
            f"Sie können mich nach Uhrzeit, Wetter, Geräten, Erinnerungen fragen "
            f"oder sagen, was ich schalten soll{_suffix()}. Einfach sprechen."
        )

    return None
