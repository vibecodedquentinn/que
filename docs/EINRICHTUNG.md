# J.Ü.R.G.E.N. — Schritt für Schritt zum laufenden System

Diese Anleitung bringt dich von „Code im Repo“ zu **Jürgen auf dem iPad**.

## Was du am Ende hast

- Eine **Website** im WLAN (z. B. `https://192.168.1.50:8443`)
- **App auf dem Home-Bildschirm** des iPads
- **Sprache + Chat** (mit konfiguriertem LLM)
- Optional **Home Assistant** und bessere **Stimme** (ElevenLabs/Piper)

---

## 1. Cursor API oder OpenAI?

**Kurz:** Für J.Ü.R.G.E.N. nutzt du **keine Cursor API**.

| | Cursor | J.Ü.R.G.E.N. |
|---|--------|----------------|
| Zweck | Cloud Agents (Code, Repos, Cursor IDE) | Haus-Chat mit Tools |
| Chat-API für eigene Apps | **Nein** (kein offizielles `/v1/chat/completions`) | Braucht OpenAI-**kompatibles** LLM |

Dein **Cursor-Abo** läuft in der IDE — es gibt keinen Key, den du hier statt OpenAI einträgst.

**Stattdessen (empfohlen):**

1. **Ollama** auf dem PC/NAS (kostenlos, lokal, Datenschutz)
2. **OpenRouter** (ein Key, viele Modelle)
3. **OpenAI / Groq** direkt

Alles funktioniert über dieselben Variablen: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.

---

## 2. Voraussetzungen

- Computer im WLAN, der **Docker** kann (Linux, Mac, Windows + WSL2)
- **iPad** im gleichen WLAN
- Optional: **Home Assistant** mit Long-Lived Token

---

## 3. Projekt vorbereiten

```bash
cd que   # dein geklontes Repo
cp .env.example .env
```

`.env` in einem Editor öffnen (mindestens Schritt 4).

---

## 4. LLM einrichten (wähle **eine** Option)

### Option A — Ollama (empfohlen)

Auf dem **gleichen Rechner** wie Docker (oder erreichbar im LAN):

```bash
# Ollama installieren: https://ollama.com
ollama pull llama3.2
ollama serve   # läuft oft schon als Dienst
```

In `.env`:

```env
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=llama3.2
LLM_API_KEY=ollama
```

**Linux ohne Docker Desktop:** statt `host.docker.internal` die LAN-IP des Ollama-Hosts, z. B. `http://192.168.1.50:11434/v1`.

### Option B — OpenRouter

Account auf [openrouter.ai](https://openrouter.ai), API-Key erstellen:

```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-...
LLM_MODEL=anthropic/claude-sonnet-4
```

### Option C — OpenAI

```env
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

### Kein LLM

Ohne Key/URL läuft **Demo-Modus** (Uhrzeit, Wetter, Demo-Lichter) — zum Testen der UI ok, für echte Gespräche nicht.

---

## 5. Persönliches (optional)

```env
ASSISTANT_NAME=J.Ü.R.G.E.N.
ASSISTANT_ACRONYM=Joint Überwachungs-Regelungs-Gebäude-Energie-Navigator
USER_TITLE=Max
PUBLIC_URL=https://192.168.1.50:8443
```

`PUBLIC_URL` = die Adresse, die du später auf dem iPad öffnest (nur zur Orientierung).

---

## 6. Home Assistant (optional)

```env
SMART_HOME_PROVIDER=homeassistant
HOMEASSISTANT_URL=http://192.168.1.20:8123
HOMEASSISTANT_TOKEN=eyJ...
```

Token: Home Assistant → Profil → **Long-Lived Access Tokens**.

Ohne HA: `SMART_HOME_PROVIDER=mock` (Demo-Geräte).

---

## 7. Starten mit Docker

```bash
docker compose build
docker compose --profile https up -d
```

- **HTTP (nur PC-Test):** http://`<IP>`:8080  
- **HTTPS (iPad + Mikro):** https://`<IP>`:8443  

IP ermitteln:

```bash
hostname -I   # Linux
# oder am Router / Systemeinstellungen
```

Health-Check:

```bash
curl -k https://127.0.0.1:8443/api/health
curl -k https://127.0.0.1:8443/api/status
```

In `status` sollte stehen: `"llm_configured": true`, `"llm_backend": "Ollama (lokal)"` o. ä.

---

## 8. iPad einrichten

1. Safari → `https://`<DEINE-IP>`:8443`
2. Zertifikatswarnung → **Details → trotzdem fortfahren** (selbstsigniert durch Caddy)
3. **Teilen** → **Zum Home-Bildschirm** → Name „Jürgen“
4. App-Icon öffnen → Vollbild
5. Mikro tippen, **Sprache** aktivieren, optional **Wake** („Hey Jürgen“)

**Mikro geht nicht?** → fast immer **kein HTTPS**. Nur `:8443` mit Caddy-Profile `https` nutzen.

---

## 9. Stimme

| `TTS_PROVIDER` | Was tun |
|----------------|---------|
| `browser` | Nichts — iPad nutzt Systemstimmen (deutsch, eher männlich wenn verfügbar) |
| `elevenlabs` | Key + `ELEVENLABS_VOICE_ID=onwK4e9ZLuTAKqWW03F9` (Daniel) |
| `piper` | Piper-HTTP-Server + `PIPER_URL=...` |

---

## 10. Ohne Docker (Entwicklung)

```bash
./scripts/dev.sh
# UI: http://127.0.0.1:5173  (nur am Rechner)

# Produktionsnah, eine URL:
./scripts/build-web.sh
./scripts/serve-web.sh
# http://0.0.0.0:8080  — iPad im LAN ohne HTTPS: Mikro kann eingeschränkt sein
```

---

## 11. Typische Probleme

| Problem | Lösung |
|---------|--------|
| Demo-KI antwortet | `LLM_*` in `.env` prüfen, Container neu starten: `docker compose up -d --force-recreate` |
| Ollama „connection refused“ | Ollama läuft? URL für Docker korrekt? Firewall Port 11434? |
| iPad Mikro tot | HTTPS `:8443`, Seite neu laden, Mikro in iOS-Einstellungen für Safari erlauben |
| HA offline | Token, URL, `http` vs `https`, gleiches WLAN |
| WebSocket getrennt | Gleiche URL für Seite und API (nicht `:5173` und `:8000` mischen in Produktion) |

---

## 12. Checkliste „fertig“

- [ ] `.env` mit LLM (Ollama/OpenRouter/OpenAI)
- [ ] `docker compose --profile https up -d`
- [ ] `/api/status` → `llm_configured: true`
- [ ] iPad: HTTPS, Home-Bildschirm, Chat antwortet intelligent
- [ ] Optional: HA-Geräte sichtbar, Tipp schaltet um
- [ ] Optional: Sprachausgabe / Wake getestet

Fertig — Jürgen ist dein Haus-Dashboard.
