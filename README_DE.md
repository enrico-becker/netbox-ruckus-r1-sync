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
- **Switch‑Ports als dcim/interfaces**
- **Interfaces und Verkabelung (idempotent, optional autoritativ)**
- **VLANs (rename‑fest aus `/venues/{venueId}/switchProfiles/vlans`)**
- WLANs / SSIDs inkl. VLAN, Verschlüsselung und PSK
- Kabelgebundene und Wireless Clients
- **IP‑Adressen (wired & wireless, interface‑gebunden bei Wired)**
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
- Wireless (WLANs & Clients)
- Cabling
- IP‑Adressen

Bestehende Objekte werden **aktualisiert statt dupliziert**, inklusive:
- VLAN‑Renames
- WLAN‑Renames
- Port‑ und IP‑Änderungen

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

### Wireless LAN – Details
![Wireless LAN Details](docs/screenshots/RUCKUS_Netbox_wireless_wireless-lans_Details.png)

### Wireless LAN – Changelog
![Wireless LAN Changelog](docs/screenshots/RUCKUS_Netbox_wireless_wireless-lans_Changelog.png)

### Wireless Links
![Wireless Links](docs/screenshots/RUCKUS_Netbox_wireless_wireless-links.png)

---

## 🗺️ Roadmap
- Integration von **RUCKUS EDGE**
- Integration von **RUCKUS IoT Controller**
- Integration von **RUCKUS WAN Gateway**

---

## 📄 Lizenz

Dieses Projekt steht unter der **Apache License, Version 2.0**.
