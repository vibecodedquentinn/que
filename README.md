# J.Ü.R.G.E.N. — Home-Assistent als Website (iPad)

**J.Ü.R.G.E.N.** = **J**oint **Ü**berwachungs-**R**egelungs-**G**ebäude-**E**nergie-**N**avigator

Website + PWA für iPad: Sprache, Chat, Smart Home, Wetter. Der Assistent heißt **Jürgen**.

📖 **Ausführliche Anleitung:** [docs/EINRICHTUNG.md](docs/EINRICHTUNG.md) (LLM, Docker, iPad, Fehlerbehebung)

## LLM: nicht Cursor, sondern …

Die **Cursor API** ist für Cloud Agents in der IDE — **kein** Chat-Endpoint für diese App.  
J.Ü.R.G.E.N. nutzt **OpenAI-kompatible** APIs:

- **Ollama** (lokal, empfohlen) — `LLM_BASE_URL=http://…:11434/v1`
- **OpenRouter**, **OpenAI**, **Groq**, …

Siehe [docs/EINRICHTUNG.md §1 und §4](docs/EINRICHTUNG.md).

## Schnellstart

```bash
cp .env.example .env
# LLM eintragen (z. B. Ollama — siehe .env.example)

docker compose build
docker compose --profile https up -d
```

iPad: `https://<LAN-IP>:8443` → **Zum Home-Bildschirm**

## Lizenz

MIT
