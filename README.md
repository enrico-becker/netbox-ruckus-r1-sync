# NetBox RUCKUS One Sync Plugin

The **NetBox RUCKUS One Sync Plugin** synchronizes inventory and network data from **RUCKUS One (Cloud)** into **NetBox**, making RUCKUS One the authoritative *source of truth* for Wi‑Fi and switching infrastructures.

It is designed for **system integrators, operators, and vendor SEs** who want a clean, automated, and reproducible documentation of RUCKUS environments.

---

## ✨ Features

### 🔄 Synchronization
- Venues
- Sites and Locations (flexible mapping)
- Access Points
- Switches
- Interfaces & cabling
- VLANs (names from `vlanUnions`)
- WLANs / SSIDs
- Wired & wireless clients
- Wireless links

### 🗺️ Venue Mapping Modes
- **sites** – Venue becomes a NetBox Site
- **locations** – Venue becomes a Location under a parent Site
- **both** – Site + child Location

### 🏷️ Authoritative Sync
- Devices
- Interfaces
- VLANs
- Wireless
- Cabling
- IPs

Existing objects are updated instead of duplicated.

### 🎯 Selective Venue Sync
- Sync all venues
- Or select specific venues using a dual‑list selector

---

## 🖼️ Screenshots
Screenshots are located in `docs/screenshots/`.

---

## 📦 Installation

### netbox‑docker
```bash
cd netbox-docker/plugins
git clone https://github.com/<your-org>/netbox-ruckus-r1-sync.git
```
Enable the plugin:
```python
PLUGINS = ["ruckus_r1_sync"]
```
```bash
docker compose build
docker compose up -d
docker compose exec netbox python manage.py migrate
```

### Bare‑Metal NetBox
```bash
pip install netbox-ruckus-r1-sync
python manage.py migrate
python manage.py collectstatic --no-input
```

---

## ⚙️ Configuration
Plugins → RUCKUS R1 Sync → Create Tenant Config → Run Sync

---

## 📄 License
Apache License 2.0
