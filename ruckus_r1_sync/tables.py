import django_tables2 as tables

from netbox.tables import NetBoxTable
from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client


class RuckusR1TenantConfigTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = RuckusR1TenantConfig
        fields = ("name", "tenant", "enabled", "last_sync_status", "last_sync")
        default_columns = ("name", "tenant", "enabled", "last_sync_status", "last_sync")


class RuckusR1SyncLogTable(NetBoxTable):
    class Meta(NetBoxTable.Meta):
        model = RuckusR1SyncLog
        fields = ("started", "finished", "status", "summary", "tenant")
        default_columns = ("started", "finished", "status", "summary", "tenant")


class RuckusR1ClientTable(NetBoxTable):
    class Meta(NetBoxTable.Meta):
        model = RuckusR1Client
        fields = ("mac", "ip_address", "hostname", "ssid", "vlan", "tenant", "venue_id")
        default_columns = ("mac", "ip_address", "hostname", "ssid", "vlan", "tenant")
