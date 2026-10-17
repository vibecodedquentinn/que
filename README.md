# J.Ü.R.G.E.N.

**J**oint **Ü**berwachungs-**R**egelungs-**G**ebäude-**E**nergie-**N**avigator — Haus-KI als Website fürs iPad.

## Nur Cloud (empfohlen — nichts lokal)

**Kein Docker auf dem Mac, kein Ollama-Download, kein `./start`.**

| Schritt | Link |
|--------|------|
| Komplett-Anleitung | **[docs/CLOUD-NUR.md](docs/CLOUD-NUR.md)** |
| OpenRouter + Render / Fly / Hetzner | dort beschrieben |
| Nur Fritz!Box aus der Cloud | [docs/FRITZBOX-CLOUD.md](docs/FRITZBOX-CLOUD.md) |

Kurz: Repo auf **Render** (Blueprint `render.yaml`) oder **Fly** (`fly.toml`) deployen, `LLM_API_KEY` setzen, HTTPS-URL auf dem iPad speichern.

---

## Lokal (nur Entwicklung)

```bash
./start
```

Ollama + kleines/lokales Modell — **nicht** für den Normalbetrieb gedacht. Siehe [docs/EINRICHTUNG.md](docs/EINRICHTUNG.md).

## Entwicklung

```bash
./scripts/dev.sh
```

## Lizenz

MIT
