from django.contrib import admin
from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client

@admin.register(RuckusR1TenantConfig)
class RuckusR1TenantConfigAdmin(admin.ModelAdmin):
    list_display = ("tenant", "api_base_url", "ruckus_tenant_id", "enabled", "last_sync", "last_sync_status")
    search_fields = ("tenant__name", "api_base_url", "ruckus_tenant_id")

@admin.register(RuckusR1SyncLog)
class RuckusR1SyncLogAdmin(admin.ModelAdmin):
    list_display = ("tenant", "started", "finished", "status", "devices", "interfaces", "vlans", "ips", "wlans", "cables", "clients")
    search_fields = ("tenant__name", "status")

@admin.register(RuckusR1Client)
class RuckusR1ClientAdmin(admin.ModelAdmin):
    list_display = ("tenant", "mac", "ip", "ssid", "vlan", "ap_serial", "last_seen")
    search_fields = ("tenant__name", "mac", "ip", "ssid", "ap_serial")
 