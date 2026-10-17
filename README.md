# J.Ü.R.G.E.N.

**J**oint **Ü**berwachungs-**R**egelungs-**G**ebäude-**E**nergie-**N**avigator — Haus-KI als Website fürs iPad.

## Zero-Setup (du musst nichts konfigurieren)

Auf einem Rechner mit **Docker**:

```bash
chmod +x start
./start
```

- Beim **ersten Start** lädt Docker automatisch Ollama + Modell (~1–2 Min.)
- **Kein** OpenAI, **kein** Cursor API, **keine** `.env` nötig
- iPad (Safari, gleiches WLAN): **`https://<IP>:8443`**
- Optional öffentlicher Link: `./start --public` → `docker compose logs cloudflared`

Details: [docs/EINRICHTUNG.md](docs/EINRICHTUNG.md)

**Nur Cloud (nichts lokal):** [docs/CLOUD.md](docs/CLOUD.md) — KI auf dem Server, Zuhause über Home Assistant Remote oder Tailscale.

## Entwicklung

```bash
./scripts/dev.sh
```

## Lizenz

MIT
