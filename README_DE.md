# NetBox RUCKUS One Sync Plugin

Das **NetBox RUCKUS One Sync Plugin** synchronisiert Inventar‑ und Netzwerkinformationen aus **RUCKUS One (Cloud)** nach **NetBox** und etabliert RUCKUS One als autoritative *Source of Truth* für WLAN‑ und Switching‑Infrastrukturen.

Das Plugin richtet sich an **Systemintegratoren, Betreiber und Hersteller‑SEs**, die RUCKUS‑Umgebungen sauber, automatisiert und Enterprise‑tauglich in NetBox dokumentieren möchten.

---

## ✨ Features

### 🔄 Synchronisation
- Venues
- Sites und Locations (flexibles Mapping)
- Access Points
- Switches
- Interfaces und Verkabelung
- VLANs inkl. Namen aus `vlanUnions`
- WLANs / SSIDs
- Kabelgebundene und Wireless Clients
- Wireless Links

### 🗺️ Venue‑Mapping
- **sites** – Venue wird ein NetBox‑Standort
- **locations** – Venue wird eine Location unter einem Parent‑Site
- **both** – Site plus Child‑Location

### 🏷️ Authoritativer Sync
RUCKUS One kann pro Objektklasse autoritativ sein:
- Devices
- Interfaces
- VLANs
- Wireless
- Cabling
- IP‑Adressen

Bestehende Objekte werden **aktualisiert statt dupliziert**, inklusive Namensänderungen.

### 🎯 Selektiver Venue‑Sync
- Alle Venues synchronisieren oder
- gezielte Auswahl über Dual‑List‑Selector

---

## 🖼️ Screenshots

### Plugin‑Konfiguration
![Configs](docs/screenshots/RUCKUS_Netbox_plugins_ruckus-r1-sync_configs.png)

### Tenant‑Konfiguration (Detail)
![Config Detail](docs/screenshots/RUCKUS_Netbox_plugins_ruckus-r1-sync_configs_1.png)

### Tenant‑Konfiguration (Bearbeiten)
![Config Edit](docs/screenshots/RUCKUS_Netbox_plugins_ruckus-r1-sync_configs_1_edit.png)

### Devices
![Devices](docs/screenshots/RUCKUS_Netbox_dcim_devices.png)

### Interfaces
![Interfaces](docs/screenshots/RUCKUS_Netbox_dcim_interfaces.png)

### Interface‑Verbindungen
![Interface Connections](docs/screenshots/RUCKUS_Netbox_dcim_interface-connections.png)

### Verkabelung
![Cabling](docs/screenshots/RUCKUS_Netbox_dcim_cables.png)

### Locations
![Locations](docs/screenshots/RUCKUS_Netbox_dcim_locations.png)

### VLANs
![VLANs](docs/screenshots/RUCKUS_Netbox_ipam_vlans.png)

### IP‑Adressen
![IPAM](docs/screenshots/RUCKUS_Netbox_ipam_ip-addresses.png)

### Wireless LANs
![Wireless LANs](docs/screenshots/RUCKUS_Netbox_wireless_wireless-lans.png)

### Wireless Links
![Wireless Links](docs/screenshots/RUCKUS_Netbox_wireless_wireless-links.png)

---

## 📦 Installation

### Voraussetzungen
- NetBox ≥ 4.0
- Python ≥ 3.10
- RUCKUS One Cloud Tenant

---

### 🔧 Installation mit netbox‑docker

```bash
cd netbox-docker/plugins
git clone https://github.com/<your-org>/netbox-ruckus-r1-sync.git
```

Plugin aktivieren (`configuration/plugins.py`):

```python
PLUGINS = [
    "ruckus_r1_sync",
]
```

```bash
docker compose build
docker compose up -d
docker compose exec netbox python manage.py migrate
```

---

### 🔧 Installation (klassisch)

```bash
source /opt/netbox/venv/bin/activate
pip install netbox-ruckus-r1-sync
python manage.py migrate
python manage.py collectstatic --no-input
```

---

## ⚙️ Konfiguration

1. **Plugins → RUCKUS R1 Sync**
2. Tenant‑Konfiguration anlegen
3. API‑Zugangsdaten und Mapping konfigurieren
4. Venues laden
5. Sync starten

---

## 📄 Lizenz

Dieses Projekt steht unter der **Apache License, Version 2.0**.  
Details siehe `LICENSE`‑Datei.
