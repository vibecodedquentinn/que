# J.Ü.R.G.E.N. — Zero-Setup

## Du musst nichts konfigurieren

Alles ist vorkonfiguriert: **Ollama**, **KI-Modell**, **Website**, **HTTPS im LAN**.

### Ein Befehl (auf einem Rechner/NAS/Raspberry Pi mit Docker)

```bash
chmod +x start
./start
```

Fertig. Öffne auf dem **iPad** (Safari, gleiches WLAN):

**https://\<IP-des-Rechners\>:8443**

(IP steht in der Ausgabe von `./start`)

**Zum Home-Bildschirm:** Teilen → *Zum Home-Bildschirm* (2 Taps — das kann kein Skript auf dem iPad ersetzen).

### iPad ohne LAN-IP suchen

```bash
./start --public
```

Dann Logs ansehen:

```bash
docker compose logs cloudflared | grep trycloudflare
```

Den **https://….trycloudflare.com** Link auf dem iPad öffnen — Mikrofon funktioniert (HTTPS).

---

## Was `./start` macht

1. Baut das Docker-Image (Website + Backend)
2. Startet **Ollama** und lädt **llama3.2:1b** (klein, schnell)
3. Startet **Jürgen** mit LLM-Anbindung (kein OpenAI, kein Cursor API)
4. Startet **Caddy** für HTTPS auf Port **8443**

---

## Cursor API?

**Nein.** Cursor hat keine Chat-API für diese App. Stattdessen läuft **Ollama im Docker** — komplett lokal.

---

## Optional (später)

Bearbeite `.env` nur wenn du willst:

- Home Assistant
- ElevenLabs-Stimme
- Anderes Ollama-Modell (`LLM_MODEL` in `docker-compose.yml`)

---

## Stoppen

```bash
docker compose --profile https --profile public down
```
