from netbox.api.serializers import NetBoxModelSerializer
from ..models import RuckusR1TenantConfig


class RuckusR1TenantConfigSerializer(NetBoxModelSerializer):
    class Meta:
        model = RuckusR1TenantConfig
        fields = [
            "id", "url", "display", "created", "last_updated",
            "tenant", "name",
            "api_base_url", "ruckus_tenant_id",
            "client_id", "client_secret",
            "enabled",
            "allow_stub_devices", "allow_stub_vlans", "allow_stub_wireless",
            "authoritative_devices", "authoritative_interfaces", "authoritative_ips",
            "authoritative_vlans", "authoritative_wireless", "authoritative_cabling",
            "default_site_group", "default_device_role", "default_manufacturer",
            "last_sync", "last_sync_status", "last_sync_message",
        ]
 