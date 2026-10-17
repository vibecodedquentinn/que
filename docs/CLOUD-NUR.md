# Alles in der Cloud — nichts lokal

**Ziel:** Auf Mac, iPad und zu Hause läuft **kein** Docker, **kein** Ollama, **kein** `./start`.  
Du nutzt Jürgen nur als **Website** (Safari → Link zum Home-Bildschirm).

| Wo | Was |
|----|-----|
| **Cloud-Server** (Render, Fly.io, Hetzner, …) | Jürgen + KI (OpenRouter) + Stimme |
| **iPad** | Nur Browser/PWA |
| **Fritz!Box** | VPN vom **Server** ins Heimnetz — [FRITZBOX-CLOUD.md](FRITZBOX-CLOUD.md) |
| **Dein Mac** | **Nichts** installieren |

---

## Schritt 1 — OpenRouter (KI, ~5 Min.)

1. Konto auf [openrouter.ai](https://openrouter.ai)
2. API-Key erstellen
3. Guthaben / Limit setzen (Pay-as-you-go)

Das ersetzt Ollama komplett — **kein 4,7‑GB-Download** auf deinen Geräten.

---

## Schritt 2 — Hosting wählen (eine Option)

### A) Render (einfach, GitHub, HTTPS inklusive)

1. [render.com](https://render.com) → **New** → **Blueprint** → Repo `que` verbinden  
2. Render liest `render.yaml` aus dem Repo  
3. Im Dashboard **Environment** setzen (aus `.env.cloud.example`):
   - `LLM_API_KEY`, `PUBLIC_URL` (= Render-URL, z. B. `https://juergen.onrender.com`)
4. **Deploy** — fertig. Link auf dem iPad öffnen.

> Free-Tier schläft nach Inaktivität — für dauerhaft „da“: kleiner Paid Plan.

### B) Fly.io

```bash
# Einmalig von **jedem** Rechner mit flyctl — oder Fly Dashboard „Deploy from GitHub“
fly launch --no-deploy
fly secrets set LLM_API_KEY=sk-or-... LLM_BASE_URL=https://openrouter.ai/api/v1 LLM_MODEL=anthropic/claude-sonnet-4 PUBLIC_URL=https://DEIN-NAME.fly.dev
fly volumes create juergen_data --size 1
fly deploy
```

Danach nur noch iPad — **kein** weiterer Dienst zu Hause.

### C) Hetzner Cloud VPS (volle Kontrolle, Fritz-VPN)

1. CX22 o. ä. bestellen (Ubuntu)  
2. **Nur auf dem VPS** (SSH in der Hetzner-Konsole, nicht „lokal“ auf dem Mac nötig):

```bash
git clone https://github.com/vibecodedquentinn/que.git
cd que
cp .env.cloud.example .env
nano .env   # Keys eintragen
docker compose -f docker-compose.cloud.yml -f docker-compose.cloud.caddy.yml up -d --build
```

3. Domain → VPS-IP, `PUBLIC_URL` und `DOMAIN` in `.env`  
4. Fritz: [FRITZBOX-CLOUD.md](FRITZBOX-CLOUD.md) (WireGuard **auf dem VPS**)

---

## Schritt 3 — iPad

1. **HTTPS-URL** aus dem Hoster öffnen (Render/Fly/Hetzner)  
2. **Teilen → Zum Home-Bildschirm**  
3. Einmal **Start** tippen (Mikrofon) — danach nur sprechen  

---

## Sicherheit

- Jürgen hat **kein Login** → Hoster-URL mit **Cloudflare Access**, **Basic Auth** (Caddy), oder Fly/Render private networking absichern  
- Keys nur im Hoster, nie ins Git  

---

## Was du **nicht** brauchst

- `./start`, Docker Desktop, Ollama auf dem Mac  
- `./start --public` (das wäre Jürgen auf **deinem** Rechner)  
- NAS / Raspberry Pi für die App  

Lokales `./start` ist nur noch für **Entwickler** — siehe `docs/EINRICHTUNG.md`.

---

## Check

`https://DEINE-URL/api/status` → `"llm_configured": true`, `"model": "anthropic/claude-sonnet-4"` (oder dein Modell).
