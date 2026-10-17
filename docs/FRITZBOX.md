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

### 3. Netzweg zur Fritz!Box

Jürgen muss die Box **technisch erreichen** (TR-064 ist kein öffentliches Web-API):

| Wo Jürgen läuft | So klappt Fritz!Box |
|-----------------|---------------------|
| Zu Hause (`./start`) | `FRITZBOX_HOST=192.168.178.1` im LAN |
| **Cloud** (VPS) | **Tailscale** ins Heimnetz (Subnet `192.168.178.0/24`) — siehe [CLOUD.md](CLOUD.md) |
| **Cloud** ohne Tailscale | Fritz über **Home Assistant** (+ Nabu Casa), nicht direkt |

**Quick-Tunnel (`./start --public`)** macht nur die **Jürgen-Website** öffentlich — **nicht** die Fritz!Box. Für „Jürgen nur in der Cloud“: [CLOUD.md](CLOUD.md).

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
