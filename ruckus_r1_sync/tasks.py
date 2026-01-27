import django_tables2 as tables
from django_tables2 import TemplateColumn

from netbox.tables import NetBoxTable
from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client


class RuckusR1TenantConfigTable(NetBoxTable):
    name = tables.Column(linkify=True)

    actions = TemplateColumn(
        template_name="ruckus_r1_sync/inc/config_actions.html",
        orderable=False,
        exclude_from_export=True,
    )

    class Meta(NetBoxTable.Meta):
        model = RuckusR1TenantConfig
        fields = (
            "actions",
            "name",
            "tenant",
            "enabled",
            "last_sync_status",
            "last_sync",
        )
        default_columns = ("actions", "name", "tenant", "enabled", "last_sync_status", "last_sync")


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
