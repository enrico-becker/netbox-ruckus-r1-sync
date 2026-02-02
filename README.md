# NetBox RUCKUS One Sync Plugin

The **NetBox RUCKUS One Sync Plugin** synchronizes inventory and network data from **RUCKUS One (Cloud)** into **NetBox**, establishing RUCKUS One as an authoritative *Source of Truth* for WLAN and switching infrastructures.

The plugin targets **system integrators, operators and vendor SEs** who want clean, automated and enterprise‑grade documentation of RUCKUS environments in NetBox.

---

## ✨ Features

### 🔄 Synchronization
- Venues
- Sites and Locations (flexible mapping)
- Access Points
- Switches
- **Switch ports as dcim/interfaces**
- **Interfaces and cabling (idempotent, optionally authoritative)**
- **VLANs (rename‑safe via `/venues/{venueId}/switchProfiles/vlans`)**
- WLANs / SSIDs incl. VLAN, encryption and PSK
- Wired and wireless clients
- **IP addresses (wired & wireless, interface‑bound for wired)**
- Wireless links

### 🗺️ Venue Mapping
- **sites** – Venue becomes a NetBox Site
- **locations** – Venue becomes a Location under a parent Site
- **both** – Site plus child Location

### 🏷️ Authoritative Sync
RUCKUS One can be authoritative per object class:
- Devices
- Interfaces
- VLANs
- Wireless (WLANs & clients)
- Cabling
- IP addresses

Objects are **updated instead of duplicated**, including renames.

---

## 🗺️ Roadmap
- Integration of **RUCKUS EDGE**
- Integration of **RUCKUS IoT Controller**
- Integration of **RUCKUS WAN Gateway**

---

## 📄 License
Apache License, Version 2.0
