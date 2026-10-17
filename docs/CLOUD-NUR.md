# Alles in der Cloud — fast zero Setup

**Mac/iPad:** nur Browser. **Kein** Docker, **kein** Ollama, **keine** Fritz!Box-Konfiguration.

---

## Einmalig (2 Minuten)

### 1. Render Blueprint

1. [render.com](https://render.com) → **New** → **Blueprint**
2. Repo **`vibecodedquentinn/que`** verbinden (Branch mit PR oder `main`)
3. Unter **Environment** **nur einen** Secret setzen:
   - **`LLM_API_KEY`** = dein [OpenRouter](https://openrouter.ai)-Key (`sk-or-…`)

Das war’s. **`PUBLIC_URL`** setzt Render automatisch (`RENDER_EXTERNAL_URL`). Modell & OpenRouter-URL sind im Blueprint vorkonfiguriert.

### 2. iPad

HTTPS-Link von Render öffnen → **Zum Home-Bildschirm** → **Start** (Mikro).

---

## Was schon eingebaut ist

| Thema | Status |
|--------|--------|
| KI | OpenRouter, Modell `openai/gpt-4o-mini` (schnell & schlau genug) |
| Schlau ohne LLM | Intent-Router: Uhrzeit, Wetter, Geräte, Follow-ups („Und in Hamburg?“), Erinnerungen |
| Stimme | Piper Thorsten (Server-TTS) |
| 3D-Gesicht | Hologramm-Kugel in der UI |
| Fritz!Box | **Aus** — optional später |

Upgrade Modell (optional in Render): `LLM_MODEL=anthropic/claude-sonnet-4`

---

## Alternativen

- **Fly.io:** `fly.toml` + `fly secrets set LLM_API_KEY=…`
- **Hetzner VPS:** `docker compose -f docker-compose.cloud.yml up -d --build` + `.env.cloud.example`

---

## Sicherheit

URL mit Cloudflare Access oder Basic Auth schützen — Jürgen hat kein Login.

Check: `https://DEINE-URL/api/status` → `llm_configured: true`
