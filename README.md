# J.Ü.R.G.E.N.

**J**oint **Ü**berwachungs-**R**egelungs-**G**ebäude-**E**nergie-**N**avigator — Haus-KI als Website fürs iPad.

## Nur Cloud (empfohlen — nichts lokal)

**Kein Docker auf dem Mac, kein Ollama-Download, kein `./start`.**

**[docs/CLOUD-NUR.md](docs/CLOUD-NUR.md)** — Render Blueprint, **nur ein** Secret (`LLM_API_KEY` von OpenRouter), Rest ist vorkonfiguriert.

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
