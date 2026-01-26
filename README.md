# NetBox RUCKUS R1 Sync Plugin

A NetBox plugin to synchronize data from **RUCKUS One (R1)** into NetBox.

This plugin is designed for documentation and inventory use cases and supports
Docker-based NetBox installations (netbox-docker).

---

## Features

- Synchronization from **RUCKUS One Public API**
- Import of:
  - Venues / Networks
  - Devices (Access Points, Switches)
  - VLANs
  - Interfaces and basic cabling relationships (where available)
- Tenant-aware imports
- Optional authoritative mode
- CLI-based synchronization
- NetBox v4 compatible (`netbox.plugins`) 

---

## Repository

https://github.com/enrico-becker/netbox-ruckus-r1-sync

---

## Requirements

- NetBox **v4.x**
- Python **3.10+**
- Docker & Docker Compose
- RUCKUS One API token

---

## Installation (Docker / netbox-docker)

### 1. Clone the plugin

```bash
cd netbox-docker/plugins
git clone https://github.com/enrico-becker/netbox-ruckus-r1-sync.git
```

Resulting structure:

```text
netbox-docker/
└── plugins/
    └── netbox-ruckus-r1-sync/
        ├── netbox_plugin_ruckus_r1_sync/
        ├── pyproject.toml
        └── README.md
```

---

### 2. Add plugin to `plugin_requirements.txt`

In your **netbox-docker** root directory, edit or create `plugin_requirements.txt`:

```text
plugins/netbox-ruckus-r1-sync
```

---

### 3. Enable the plugin

Edit `configuration/plugins.py`:

```python
PLUGINS = [
    "netbox_plugin_ruckus_r1_sync",
]

PLUGINS_CONFIG = {
    "netbox_plugin_ruckus_r1_sync": {
        "api_base_url": "https://api.ruckus.cloud",
        "api_token": "YOUR_RUCKUS_ONE_API_TOKEN",
        "default_tenant": None,
        "authoritative": False,
        "allow_stub_devices": True,
    }
}
```

---

### 4. Build and start NetBox

```bash
docker compose build
docker compose up -d
```

Verify plugin loading:

```bash
docker compose logs netbox | grep ruckus
```

---

## Running a Sync

The plugin provides a Django management command.

Basic sync:

```bash
docker compose exec netbox python manage.py ruckus_r1_sync
```

Example with options:

```bash
docker compose exec netbox python manage.py ruckus_r1_sync \
  --tenant-id 11 \
  --authoritative
```

---

## Configuration Options

| Option | Description |
|------|------------|
| `api_base_url` | RUCKUS One API base URL |
| `api_token` | API authentication token |
| `default_tenant` | Fallback tenant ID |
| `authoritative` | Overwrite NetBox objects |
| `allow_stub_devices` | Create placeholder devices |

---

## Development Notes

- Compatible with NetBox v4+
- Uses `netbox.plugins`
- Does not override global navigation or dashboard routes
- Safe for multi-tenant environments

---

## Roadmap

- Full interface and cable relationship sync
- WLAN / SSID objects
- Scheduled sync jobs
- Web-based configuration UI
- Extended statistics and client data (optional)

---

## Disclaimer

This project is **not officially supported** by CommScope or RUCKUS Networks.  
Provided as-is for lab, PoC, and documentation purposes.

---

## License

MIT License

---

## Author

**Enrico Becker**  
System Engineer
GitHub: https://github.com/enrico-becker
