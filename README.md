# NetBox RUCKUS One Sync Plugin (`ruckus_r1_sync`)

Dieses NetBox-Plugin synchronisiert Inventar-, WLAN- und Client-Daten aus **RUCKUS One (Cloud)** nach **NetBox**.  
Es richtet sich an Systemintegratoren, Betreiber und Hersteller-SEs, die RUCKUS-Umgebungen strukturiert dokumentieren und automatisiert aktuell halten wollen.

---

## ✨ Features (aktueller Stand)

### 🔄 Synchronisation
- RUCKUS One Venues
- Access Points
- Switches
- Interfaces
- WLANs
- WLAN- & Wired-Clients
- Cabling / Links (optional, authoritativ)
- Multi-Tenant-fähig (NetBox Tenants)

---

### 🗺️ Venue Mapping Roadmap (implementiert)

Venues aus RUCKUS One können flexibel in NetBox abgebildet werden:

| Modus | Beschreibung |
|------|-------------|
| `sites` | Jede Venue wird ein **NetBox Site** |
| `locations` | Jede Venue wird eine **Location** unter einem bestehenden Parent-Site |
| `both` | Venue wird ein **Site** + darunter eine **Location** |

Konfigurierbar **pro Tenant** über die UI.

---

### 🎯 Venue Selection Roadmap (implementiert)

- Venues können **gezielt für den Sync ausgewählt** werden
- Komfortable **Dual-List UI**:
  - links: *Available Venues*
  - rechts: *Selected for Sync*
- **Leere Auswahl = alle Venues synchronisieren** (Default-Verhalten)
- Neue Venues aus RUCKUS One erscheinen automatisch links
- Auswahl wird persistent gespeichert

---

## 🧩 Voraussetzungen

- NetBox **4.5.x**
- Docker / netbox-docker
- RUCKUS One Tenant
- Python 3.12 (NetBox Standard)

---

## 📦 Installation

### 1. Plugin ins NetBox-Plugins-Verzeichnis legen
```bash
/plugins/netbox-ruckus-r1-sync/
```

### 2. Plugin aktivieren

`configuration/plugins.py`:

```python
PLUGINS = [
    "ruckus_r1_sync",
]

PLUGINS_CONFIG = {
    "ruckus_r1_sync": {
        "verify_tls": True,
        "request_timeout": 30,
    }
}
```

---

### 3. Migrationen ausführen
```bash
docker compose exec netbox bash -lc "python manage.py migrate ruckus_r1_sync"
```

---

### 4. Static Files einsammeln (wichtig!)
```bash
docker compose exec -u root netbox bash -lc "python manage.py collectstatic --no-input"
```

---

### 5. NetBox neu starten
```bash
docker compose restart netbox netbox-worker
```

---

## ⚙️ Konfiguration (UI)

Pfad:
```
Plugins → RUCKUS R1 Sync → Tenant Configs
```

### Wichtige Felder

#### RUCKUS API
- **API Base URL** – Region (EU/US/APAC)
- **Tenant ID**
- **Client ID / Client Secret**

#### Venue Mapping
- **Venue Mapping Mode**
  - `sites`
  - `locations`
  - `both`
- **Parent Site** (nur bei `locations`)
- **Child Location Name** (nur bei `both`)

#### Venue Selection
- **Venues selected for Sync**
  - leer = alle Venues
  - Auswahl per Dual-List Selector

---

## 🧠 Wichtige Logik

- **Keine Venue ausgewählt** → alle Venues werden synchronisiert
- **Venues ausgewählt** → nur diese werden synchronisiert
- Mapping & Selection gelten **pro Tenant**
- Refresh Venues lädt Metadaten aus RUCKUS One, ohne Sync auszulösen

---

## 🔍 Debug / Checks

### Venue Cache prüfen
```bash
docker compose exec netbox bash -lc "python manage.py shell -c \
\"from ruckus_r1_sync.models import RuckusR1TenantConfig as C; c=C.objects.first(); print(len(c.venues_cache))\""
```

### Ausgewählte Venues prüfen
```bash
docker compose exec netbox bash -lc "python manage.py shell -c \
\"from ruckus_r1_sync.models import RuckusR1TenantConfig as C; c=C.objects.first(); print(c.venues_selected)\""
```

---

## 🚧 Roadmap (Ausblick)

- Dry-Run Sync
- Delta-Sync pro Venue
- Sync-Log mit Venue-Filter
- Bulk-Actions ("Sync only this Venue")
- API-basierte Steuerung

---

## 👤 Autor

Enrico Becker  
System Engineer – RUCKUS Networks  
