# Jürgen in der Cloud (nicht zu Hause)

Du kannst **Jürgen komplett in der Cloud** betreiben — kein Docker auf dem Mac, kein NAS, kein Raspberry Pi **für die App**.

Was **nicht** geht: Die Fritz!Box-API direkt aus dem Internet aufrufen, als wäre sie eine Website. AVM öffnet TR-064 absichtlich **nicht** nach außen.

Was **geht**: Jürgen läuft auf einem Server (Hetzner, Fly.io, Railway, …) und erreicht dein Zuhause über einen **sicheren Kanal** — ohne dass Jürgen bei dir lokal läuft.

## Architektur

| Ziel | Lösung |
|------|--------|
| Sprache, KI, iPad-UI | Cloud-Server + `docker-compose.cloud.yml` |
| **Nur Fritz!Box** (kein HA) | **[FRITZBOX-CLOUD.md](FRITZBOX-CLOUD.md)** — WireGuard-VPN der Fritz!Box zum VPS |
| Fritz + Lampen etc. | Home Assistant + Nabu Casa (optional) |

---

## 1. Jürgen in der Cloud starten

### `.env` auf dem Server

```env
PUBLIC_URL=https://juergen.deine-domain.de

# KI in der Cloud (Ollama geht nur, wenn du Ollama auf demselben Server betreibst)
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...
LLM_MODEL=anthropic/claude-sonnet-4

# Smart Home — bei „nur Fritz!Box“: mock lassen
SMART_HOME_PROVIDER=mock

# Fritz!Box: siehe FRITZBOX-CLOUD.md (VPN + FRITZBOX_*)
FRITZBOX_ENABLED=true
FRITZBOX_HOST=192.168.178.1
```

Start:

```bash
docker compose -f docker-compose.cloud.yml up -d --build
```

Vor dem iPad: **HTTPS** (Reverse-Proxy mit Let’s Encrypt, Caddy, nginx) und `PUBLIC_URL` setzen — sonst kein Mikrofon in Safari.

### Sicherheit

Jürgen hat **kein Login**. In der Cloud **unbedingt** absichern:

- Cloudflare Tunnel + **Access** (E-Mail-Login)
- oder Basic Auth vor dem Reverse-Proxy
- oder VPN (Tailscale) nur für dein iPad

Passwörter (Fritz, HA-Token, LLM-Key) nur in `.env` auf dem Server.

---

## 2. Heimnetz ohne lokalen Jürgen

### Nur Fritz!Box → [FRITZBOX-CLOUD.md](FRITZBOX-CLOUD.md)

WireGuard (oder IPsec) **von der Fritz!Box zum VPS**, dann `docker-compose.cloud.fritz.yml` und `FRITZBOX_*` in `.env`.

### Optional: Home Assistant + Nabu Casa

Wenn du später HA hast: `HOMEASSISTANT_URL` + Token in `.env`, `SMART_HOME_PROVIDER=homeassistant`.

### Nicht für Cloud: `./start --public`

Quick-Tunnel = Jürgen läuft **lokal** auf deinem Rechner; Fritz!Box wird trotzdem nicht erreicht.

---

## 3. Checkliste

| Schritt | Erledigt |
|---------|----------|
| VPS / Hosting mit Docker | |
| HTTPS + `PUBLIC_URL` | |
| `LLM_*` (OpenRouter/OpenAI) | |
| Fritz-VPN (WireGuard) **oder** HA Remote | |
| iPad: Link zum Home-Bildschirm | |

Status: `https://deine-url/api/status` → `llm_configured`, `homeassistant_connected` / `fritzbox_connected`.

---

## Kurzantwort

**Ja, Jürgen kann in der Cloud laufen.** **Nur Fritz!Box:** VPN der Box zum VPS — siehe **[FRITZBOX-CLOUD.md](FRITZBOX-CLOUD.md)**. Kein Port-Forward der Fritz-API ins Internet, kein Jürgen zu Hause.
