# Fritz!Box (und „etc.“) an Jürgen anbinden

Ja — Jürgen kann **direkt** mit deiner **AVM Fritz!Box** sprechen (Heimnetz, Internet, Gast-WLAN).  
Für **Steckdosen, DECT, Zigbee, Hue** usw. ist **Home Assistant** oft besser (eine zentrale Schaltzentrale).

## Was Jürgen an der Fritz!Box kann

| Sprache / Befehl | Aktion |
|------------------|--------|
| „Wer ist im WLAN?“ | Liste aktiver Geräte (Name, IP) |
| „Wie ist der Internetstatus?“ | WAN verbunden, externe IP |
| „Gast-WLAN an/aus“ | Gast-WLAN schalten |

Weitere Aktionen (Portfreigaben, Kindersicherung, Reconnect) können ergänzt werden — sag Bescheid.

## Einrichtung (5 Minuten)

### 1. Fritz!Box-Benutzer anlegen

In der Fritz!Box-Oberfläche:

**System → FRITZ!Box-Benutzer → Benutzer anlegen**

- Recht: **FRITZ!Box-Einstellungen** und **Smart Home** (falls vorhanden)
- Starkes Passwort notieren

> Bei älteren Firmwares reicht oft nur das **Fritz!Box-Passwort** ohne extra User (`FRITZBOX_USER` leer lassen).

### 2. `.env` ergänzen

```env
FRITZBOX_ENABLED=true
FRITZBOX_HOST=192.168.178.1
FRITZBOX_USER=JürgenAPI
FRITZBOX_PASSWORD=dein-passwort
```

`FRITZBOX_HOST` = IP deiner Box (Standard oft `192.168.178.1`).

### 3. Docker / Server im **gleichen LAN**

Jürgen muss die Fritz!Box **im Heimnetz** erreichen:

- Docker Desktop: `FRITZBOX_HOST=192.168.178.1` geht meist direkt
- Linux Docker: ggf. `network_mode: host` oder IP des Hosts nutzen

**Cloud-Tunnel (trycloudflare)** kann **keine** Fritz!Box in deinem LAN sehen — dafür Jürgen **zu Hause** mit `./start` laufen lassen.

### 4. Neustart

```bash
docker compose up -d --force-recreate
# oder ./start
```

Status prüfen: `/api/status` → `"fritzbox_connected": true`

## Home Assistant statt direkt?

Wenn du schon **Home Assistant** hast:

```env
SMART_HOME_PROVIDER=homeassistant
HOMEASSISTANT_URL=http://...
HOMEASSISTANT_TOKEN=...
```

Dann steuerst du Fritz!Box **und** alles andere (Hue, Shelly, …) über HA — Jürgen nutzt dieselben Geräte.

## Sicherheit

- Passwort **nur** in `.env`, nie ins Git
- Jürgen nur im **eigenen WLAN** oder hinter VPN betreiben
- Kein Port-Forward der Fritz!Box-API ins Internet
