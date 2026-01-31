# NetBox RUCKUS One Sync Plugin

Das **NetBox RUCKUS One Sync Plugin** synchronisiert Inventar‑ und Netzwerkinformationen aus **RUCKUS One (Cloud)** nach **NetBox** und macht RUCKUS One zur *Source of Truth* für WLAN‑ und Switching‑Infrastrukturen.

---

## ✨ Features
- Venues
- Sites & Locations
- Access Points & Switches
- Interfaces, VLANs, WLANs
- Clients & Wireless Links

---

## 📦 Installation

### netbox‑docker
```bash
cd netbox-docker/plugins
git clone https://github.com/<your-org>/netbox-ruckus-r1-sync.git
docker compose build
docker compose up -d
docker compose exec netbox python manage.py migrate
```

### Klassisch
```bash
pip install netbox-ruckus-r1-sync
python manage.py migrate
```

---

## 📄 Lizenz
MIT
