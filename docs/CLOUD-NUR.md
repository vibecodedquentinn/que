# Alles in der Cloud — ohne Kosten-Falle

**Mac/iPad:** nur Browser. **Kein** Docker, **kein** Ollama zu Hause.

---

## Was **0 €** kostet

### A) Ganz ohne KI-Key (schon eingebaut)

Jürgen beantwortet **ohne** OpenRouter viel per Intent-Router — **unbegrenzt**, **kostenlos**:

- Uhrzeit, Datum  
- Wetter (+ „Und in Hamburg?“)  
- Geräte schalten, „alle Lichter aus“  
- Erinnerungen, Notizen  
- Danke, Hilfe, Kurzantworten  

Du kannst Render deployen und **keinen** `LLM_API_KEY` setzen — für den Alltag reicht das oft.

### B) OpenRouter **gratis** (für freie Gespräche)

OpenRouter ist **nicht** automatisch kostenpflichtig:

- Konto anlegen → **API-Key** (kostenlos)  
- Modell **`openrouter/free`** (Standard im Blueprint) → **0 €** pro Anfrage  
- Limits laut OpenRouter: ca. **50 Anfragen/Tag** auf Free-Modellen (reicht für Smalltalk neben dem Intent-Router)  

**Keine Kreditkarte nötig**, solange du nur **`:free`** / **`openrouter/free`** nutzt.

Optional später (kostet): z. B. `LLM_MODEL=openai/gpt-4o-mini` + Guthaben aufladen.

### C) Groq (Alternative, Free Tier)

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile
```

Groq hat ein **kostenloses Kontingent** — Key auf [console.groq.com](https://console.groq.com).

---

## Einmalig deployen (Render)

1. [render.com](https://render.com) → **Blueprint** → Repo **`vibecodedquentinn/que`**
2. **Optional:** `LLM_API_KEY` = OpenRouter-Key (für Free-Modell + Smalltalk)  
   - **Weglassen** = nur Intent-Router (siehe oben)
3. iPad: HTTPS-Link → Home-Bildschirm → **Start**

`PUBLIC_URL` kommt von Render automatisch. Standard-Modell: **`openrouter/free`**.

---

## Eingebaut

| Thema | Status |
|--------|--------|
| KI (optional) | OpenRouter **`openrouter/free`** — 0 € |
| Schlau ohne KI | Intent-Router + Session-Kontext |
| Stimme | Piper Thorsten |
| UI | 3D-Hologramm |

---

## Sicherheit

Hosting-URL absichern (Cloudflare Access o. ä.) — Jürgen hat kein Login.

Status: `/api/status` → ohne Key: `llm_configured: false`, Router trotzdem nutzbar.
