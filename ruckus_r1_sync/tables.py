from __future__ import annotations

import django_tables2 as tables
from netbox.tables import NetBoxTable

from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client


class RuckusR1TenantConfigTable(NetBoxTable):
    tenant = tables.Column(linkify=True)
    name = tables.Column(linkify=True)
    enabled = tables.BooleanColumn()
    venue_mapping_mode = tables.Column(verbose_name="Mapping")
    venue_locations_parent_site = tables.Column(verbose_name="Parent site")
    sync_vlans = tables.BooleanColumn(verbose_name="VLANs")
    sync_wlans = tables.BooleanColumn(verbose_name="WLANs")
    sync_aps = tables.BooleanColumn(verbose_name="APs")
    sync_switches = tables.BooleanColumn(verbose_name="Switches")
    last_sync_status = tables.Column(verbose_name="Last status")
    last_sync = tables.DateTimeColumn(verbose_name="Last sync")

    class Meta(NetBoxTable.Meta):
        model = RuckusR1TenantConfig
        fields = (
            "pk",
            "tenant",
            "name",
            "enabled",
            "venue_mapping_mode",
            "venue_locations_parent_site",
            "sync_vlans",
            "sync_wlans",
            "sync_aps",
            "sync_switches",
            "last_sync_status",
            "last_sync",
        )
        default_columns = (
            "tenant",
            "name",
            "enabled",
            "venue_mapping_mode",
            "venue_locations_parent_site",
            "sync_vlans",
            "sync_wlans",
            "sync_aps",
            "sync_switches",
            "last_sync_status",
            "last_sync",
        )


class RuckusR1SyncLogTable(NetBoxTable):
    tenant = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = RuckusR1SyncLog
        fields = ("pk", "tenant", "started", "finished", "status")
        default_columns = ("tenant", "started", "finished", "status")


class RuckusR1ClientTable(NetBoxTable):
    tenant = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = RuckusR1Client
        fields = ("pk", "tenant", "venue", "mac", "ip", "connection_type", "last_seen")
        default_columns = ("tenant", "venue", "mac", "ip", "connection_type", "last_seen")
