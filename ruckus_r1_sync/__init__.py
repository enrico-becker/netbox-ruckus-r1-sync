from netbox.plugins import PluginConfig


class RuckusR1SyncConfig(PluginConfig):
    name = "ruckus_r1_sync"
    verbose_name = "RUCKUS Networks - RUCKUS ONE to Netbox Sync"
    description = "Synchronize RUCKUS One (R1) objects into NetBox"
    version = "0.1.0"
    author = "Enrico Becker"
    base_url = "ruckus-r1-sync"
    min_version = "4.0.0"

    # IMPORTANT: relative to module ruckus_r1_sync (package)
    menu = "navigation.menu"
    api_urls = "api.urls"


config = RuckusR1SyncConfig
 