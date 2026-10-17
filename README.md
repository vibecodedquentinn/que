# J.A.R.V.I.S. Home — persönliche Home-KI

Ein lauffähiger Prototyp einer **J.A.R.V.I.S.-artigen Home-Assistentin**: Sprache & Chat, Tool-Aufrufe (Wetter, Uhrzeit, Smart Home, Notizen, Erinnerungen), futuristisches UI und optional Anbindung an ein OpenAI-kompatibles LLM.

> **Hinweis:** Echte Smart-Home-Hardware (Home Assistant, Philips Hue, MQTT, …) ist als **mockbare Schicht** vorbereitet (`backend/app/tools/devices.py`). Du kannst dort deine Integration einhängen.

## Features

- **Chat + WebSocket-Streaming** mit JARVIS-Persönlichkeit (Deutsch standardmäßig)
- **Spracheingabe** (Browser Web Speech API) und **Sprachausgabe**
- **Wake-Modus** („Hey JARVIS …“ — browserabhängig, am besten Chrome/Edge)
- **Tools:** Uhrzeit, Wetter ([wttr.in](https://wttr.in)), Smart-Home-Demo, Erinnerungen, Notizen
- **Gedächtnis:** SQLite pro Session
- **Demo ohne API-Key:** einfache Befehle per Fallback-Logik

## Schnellstart (Entwicklung)

```bash
cp .env.example .env
# Optional: OPENAI_API_KEY=sk-... eintragen

chmod +x scripts/dev.sh
./scripts/dev.sh
```

- UI: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- API: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### Manuell

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload --port 8000

cd frontend && npm install && npm run dev
```

## Konfiguration (`.env`)

| Variable | Beschreibung |
|----------|--------------|
| `OPENAI_API_KEY` | API-Key für volle LLM-Konversation |
| `OPENAI_BASE_URL` | z. B. `http://localhost:11434/v1` für Ollama |
| `OPENAI_MODEL` | Modellname |
| `USER_TITLE` | Anrede (Standard: „Sir“) |
| `DEFAULT_LANGUAGE` | `de` oder `en` |

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Frontend: Port **5173** (nginx), Backend: **8000**.

## Architektur

```
frontend (React/Vite)  ←WebSocket/REST→  backend (FastAPI)
                                              ├─ LLM + Tool Calling
                                              ├─ SQLite (Chat)
                                              └─ JSON-Dateien (Geräte, Notizen, …)
```

## Nächste Schritte (für „echtes“ JARVIS)

1. **Home Assistant** REST/WebSocket in `devices.py` anbinden
2. **Wake Word offline** (z. B. openWakeWord + lokales STT)
3. **Lokales LLM** über Ollama (`OPENAI_BASE_URL`)
4. **Routinen & Automationen** (Cron, Geofencing)
5. **Multi-Raum-Audio** (satellite clients)

## Lizenz

MIT — baue frei darauf auf.
