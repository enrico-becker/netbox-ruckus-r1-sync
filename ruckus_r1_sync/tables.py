from __future__ import annotations

import django_tables2 as tables
from netbox.tables import NetBoxTable

from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client


class RuckusR1TenantConfigTable(NetBoxTable):
    # Name klickt direkt auf Edit (vermeidet TemplateDoesNotExist für Detail)
    name = tables.Column(linkify=("plugins:ruckus_r1_sync:ruckusr1tenantconfig_edit", {"pk": tables.A("pk")}))
    tenant = tables.Column(linkify=True)

    actions = tables.TemplateColumn(
        template_code="""
        <div class="btn-group btn-group-sm" role="group">
          <a class="btn btn-outline-primary"
             href="{% url 'plugins:ruckus_r1_sync:ruckusr1tenantconfig_edit' pk=record.pk %}">
             Edit
          </a>
          <a class="btn btn-outline-danger"
             href="{% url 'plugins:ruckus_r1_sync:ruckusr1tenantconfig_delete' pk=record.pk %}">
             Delete
          </a>
        </div>
        """,
        orderable=False,
    )

    class Meta(NetBoxTable.Meta):
        model = RuckusR1TenantConfig
        fields = (
            "pk",
            "id",
            "tenant",
            "name",
            "api_base_url",
            "enabled",
            "last_sync",
            "last_sync_status",
            "actions",
        )
        default_columns = (
            "tenant",
            "name",
            "api_base_url",
            "enabled",
            "last_sync",
            "last_sync_status",
            "actions",
        )


class RuckusR1SyncLogTable(NetBoxTable):
    tenant = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = RuckusR1SyncLog
        actions = False  # IMPORTANT: no edit/delete actions

        fields = (
            "pk",
            "id",
            "tenant",
            "started",
            "finished",
            "status",
            "clients",
            "devices",
            "ips",
            "error",
        )
        default_columns = ("tenant", "started", "status", "clients", "devices", "ips", "error")


class RuckusR1ClientTable(NetBoxTable):
    tenant = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = RuckusR1Client
        actions = False  # IMPORTANT: no edit/delete actions

        fields = (
            "pk",
            "id",
            "tenant",
            "mac",
            "ip_address",
            "hostname",
            "ssid",
            "venue_id",
            "network_id",
            "ruckus_id",
            "last_seen",
        )
        default_columns = ("tenant", "mac", "ip_address", "hostname", "ssid", "last_seen")
 