# J.Ü.R.G.E.N. — Home-Assistent als Website (iPad)

**J.Ü.R.G.E.N.** steht für:

**J**ntelligentes **Ü**berwachungs-**R**outine-**G**ebäude-**E**nergie-**N**etzwerk

Eine **Website**, die du auf dem **iPad** wie eine App nutzen kannst: Sprache, Chat, Smart Home, Wetter, Erinnerungen. Der Assistent stellt sich als **Jürgen** vor — ruhig, sachlich, professionell.

## iPad schnell starten

```bash
cp .env.example .env
docker compose build
docker compose --profile https up -d
```

Safari: `https://<DEINE-IP>:8443` → **Teilen → Zum Home-Bildschirm**

> Mikrofon auf dem iPad: nur mit **HTTPS** (Caddy-Profile `https`).

## Entwicklung

```bash
./scripts/dev.sh
./scripts/build-web.sh && ./scripts/serve-web.sh   # eine URL :8080
```

## Stimme

| Modus | Beschreibung |
|--------|----------------|
| `browser` | Kostenlos; bevorzugt deutsche Männerstimmen (Thorsten/Hans/Markus), tieferer Ton |
| `elevenlabs` | Standard: **Daniel** (`onwK4e9ZLuTAKqWW03F9`) — ruhig, professionell, Deutsch |
| `piper` | **Thorsten** (`de_DE-thorsten-high`) über eigenen Piper-HTTP-Server |

## Konfiguration

| Variable | Zweck |
|----------|--------|
| `ASSISTANT_NAME` / `ASSISTANT_ACRONYM` | Anzeige & KI-Persönlichkeit |
| `USER_TITLE` | Anrede (z. B. `Max`); leer = höfliches „Sie“ |
| `OPENAI_API_KEY` | Volle Konversation |
| `SMART_HOME_PROVIDER` | `mock` oder `homeassistant` |

Wake-Phrase: **„Hey Jürgen“**

## Lizenz

MIT
