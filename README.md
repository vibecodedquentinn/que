# J.A.R.V.I.S. Home — Website für iPad & Browser

Eine **einzige Website**, die du auf dem **iPad** (Safari → *Zum Home-Bildschirm*) wie eine App nutzen kannst: Chat, Sprache, Smart Home, Wetter, Erinnerungen.

## iPad schnell starten (empfohlen)

1. Auf einem Rechner im gleichen WLAN:

```bash
cp .env.example .env
# Optional: OPENAI_API_KEY, Home Assistant, TTS

docker compose build
docker compose --profile https up -d
```

2. Auf dem **iPad** in Safari öffnen:

`https://<DEINE-IP>:8443`

(Caddy nutzt `tls internal` — Safari einmal „Fortfahren“ bestätigen.)

3. **Teilen → Zum Home-Bildschirm** → JARVIS startet im Vollbild.

> **Mikrofon auf dem iPad:** Apple erlaubt Spracheingabe im Browser nur über **HTTPS** (oder localhost). Deshalb der Caddy-Profile `https`.

## Entwicklung

```bash
./scripts/dev.sh          # Backend :8000 + Frontend :5173 (Hot Reload)
./scripts/build-web.sh    # Baut UI nach backend/static — eine URL
cd backend && uvicorn app.main:app --port 8000   # dann nur :8000
```

## Konfiguration

| Variable | Zweck |
|----------|--------|
| `OPENAI_API_KEY` | Volle KI-Konversation |
| `OPENAI_BASE_URL` | z. B. `http://localhost:11434/v1` (Ollama) |
| `SMART_HOME_PROVIDER` | `mock` oder `homeassistant` |
| `HOMEASSISTANT_URL` / `HOMEASSISTANT_TOKEN` | Long-Lived Token aus HA |
| `TTS_PROVIDER` | `browser` (iPad), `elevenlabs`, `piper` |
| `PUBLIC_URL` | Anzeige/Hinweise für deine LAN-URL |

### Home Assistant

1. Profil → Long-Lived Access Tokens → Token erstellen  
2. In `.env`: `SMART_HOME_PROVIDER=homeassistant`, URL + Token setzen  
3. Geräte erscheinen live; KI nutzt `entity_id` (z. B. `light.wohnzimmer`)

### Stimme

- **browser** — kostenlos, auf dem iPad sofort (Sprachausgabe-Toggle)
- **elevenlabs** — `TTS_PROVIDER=elevenlabs` + API-Key
- **piper** — eigener Piper-HTTP-Server, `PIPER_URL=...` (Wyoming/Piper-Container optional via `docker compose --profile piper`)

## Architektur

```
iPad Safari (PWA)
       │
       ▼
  Caddy :8443 HTTPS  ──optional──
       │
       ▼
  FastAPI :8000  ── /api, /ws, statische Website (React)
       ├── LLM + Tools
       ├── Home Assistant REST
       └── SQLite + JSON-Daten
```

## Features

- PWA (offline Shell, App-Icon)
- Touch-optimiertes UI, Safe Areas
- WebSocket-Chat, Streaming
- Gerätepanel antippen zum Schalten
- Demo-Modus ohne API-Key

## Lizenz

MIT
