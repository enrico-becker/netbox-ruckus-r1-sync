from netbox.api.serializers import NetBoxModelSerializer
from ..models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client


class RuckusR1TenantConfigSerializer(NetBoxModelSerializer):
    class Meta:
        model = RuckusR1TenantConfig
        fields = [
            "id", "url", "display", "created", "last_updated",
            "tenant", "name",
            "api_base_url", "ruckus_tenant_id",
            "client_id", "client_secret",
            "enabled",

            # sync toggles
            "sync_wlans", "sync_vlans", "sync_aps", "sync_switches",
            "sync_wifi_clients", "sync_wired_clients",
            "sync_interfaces", "sync_cabling", "sync_wireless_links",

            # behavior flags
            "allow_stub_devices", "allow_stub_vlans", "allow_stub_wireless",
            "authoritative_devices", "authoritative_interfaces", "authoritative_ips",
            "authoritative_vlans", "authoritative_wireless", "authoritative_cabling",
            "default_site_group", "default_device_role", "default_manufacturer",
            "last_sync", "last_sync_status", "last_sync_message",
        ]


class RuckusR1SyncLogSerializer(NetBoxModelSerializer):
    class Meta:
        model = RuckusR1SyncLog
        fields = [
            "id", "url", "display", "created", "last_updated",
            "tenant",
            "status", "summary", "message", "error",
            "started", "finished",
            "venues", "networks", "devices", "interfaces", "macs", "vlans", "ips",
            "wlans", "wlan_groups", "tunnels", "cables", "clients",
        ]


class RuckusR1ClientSerializer(NetBoxModelSerializer):
    class Meta:
        model = RuckusR1Client
        fields = [
            "id", "url", "display", "created", "last_updated",
            "tenant",
            "mac", "ip_address", "hostname", "ssid", "vlan",
            "venue_id", "network_id", "ruckus_id",
            "last_seen",
        ]
