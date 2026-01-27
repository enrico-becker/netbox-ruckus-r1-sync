# NetBox RUCKUS One Sync Plugin (`ruckus_r1_sync`)

This NetBox plugin synchronizes inventory, WLAN, and client data from **RUCKUS One (Cloud)** into **NetBox**.  
It is designed for system integrators, operators, and vendor SEs who want to document and maintain RUCKUS environments in a structured and automated way.

---

## ✨ Features (current status)

### 🔄 Synchronization
- RUCKUS One Venues
- Access Points
- Switches
- Interfaces
- WLANs
- Wireless & wired clients
- Cabling / links (optional, authoritative)
- Multi-tenant capable (NetBox Tenants)

---

### 🗺️ Venue Mapping Roadmap (implemented)

Venues from RUCKUS One can be flexibly mapped into NetBox:

| Mode | Description |
|------|-------------|
| `sites` | Each venue is created as a **NetBox Site** |
| `locations` | Each venue is created as a **Location** under an existing parent site |
| `both` | The venue is created as a **Site** with a **Location** underneath |

Configurable **per tenant** via the UI.

---

### 🎯 Venue Selection Roadmap (implemented)

- Venues can be **explicitly selected** for synchronization
- User-friendly **dual-list selector UI**:
  - left: *Available Venues*
  - right: *Selected for Sync*
- **Empty selection = sync ALL venues** (default behavior)
- New venues from RUCKUS One automatically appear in the available list
- Selection is persisted per tenant

---

## 🧩 Requirements

- NetBox **4.5.x**
- Docker / netbox-docker
- RUCKUS One tenant
- Python 3.12 (NetBox default)

---

## 📦 Installation

### 1. Place the plugin into the NetBox plugins directory
```bash
/plugins/netbox-ruckus-r1-sync/
```

### 2. Enable the plugin

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

### 3. Run database migrations
```bash
docker compose exec netbox bash -lc "python manage.py migrate ruckus_r1_sync"
```

---

### 4. Collect static files (important!)
```bash
docker compose exec -u root netbox bash -lc "python manage.py collectstatic --no-input"
```

---

### 5. Restart NetBox
```bash
docker compose restart netbox netbox-worker
```

---

## ⚙️ Configuration (UI)

Path:
```
Plugins → RUCKUS R1 Sync → Tenant Configs
```

### Key settings

#### RUCKUS API
- **API Base URL** – region (EU / US / APAC)
- **Tenant ID**
- **Client ID / Client Secret**

#### Venue Mapping
- **Venue Mapping Mode**
  - `sites`
  - `locations`
  - `both`
- **Parent Site** (required for `locations`)
- **Child Location Name** (used for `both`)

#### Venue Selection
- **Venues selected for Sync**
  - empty = sync all venues
  - selection via dual-list selector

---

## 🧠 Important behavior

- **No venue selected** → all venues are synchronized
- **Specific venues selected** → only those venues are synchronized
- Mapping and selection are applied **per tenant**
- “Refresh Venues” only updates metadata from RUCKUS One and does **not** trigger a sync

---

## 🔍 Debug / Checks

### Check venue cache
```bash
docker compose exec netbox bash -lc "python manage.py shell -c \
\"from ruckus_r1_sync.models import RuckusR1TenantConfig as C; c=C.objects.first(); print(len(c.venues_cache))\""
```

### Check selected venues
```bash
docker compose exec netbox bash -lc "python manage.py shell -c \
\"from ruckus_r1_sync.models import RuckusR1TenantConfig as C; c=C.objects.first(); print(c.venues_selected)\""
```

---

## 🚧 Roadmap (outlook)

- Dry-run synchronization
- Per-venue delta sync
- Sync logs with venue filtering
- Bulk actions (e.g. “Sync only this venue”)
- API-based control

---

## 👤 Author

Enrico Becker  
