from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from netbox.views import generic

from .forms import RuckusR1TenantConfigForm
from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client
from .tables import RuckusR1TenantConfigTable, RuckusR1SyncLogTable, RuckusR1ClientTable
from .sync import run_sync_for_tenantconfig, _make_client, _query_all


class RuckusR1TenantConfigListView(generic.ObjectListView):
    queryset = RuckusR1TenantConfig.objects.all()
    table = RuckusR1TenantConfigTable


class RuckusR1TenantConfigView(generic.ObjectView):
    queryset = RuckusR1TenantConfig.objects.all()
    template_name = "ruckus_r1_sync/ruckusr1tenantconfig.html"
    object_fields = (
        ("General", ("tenant", "name", "enabled")),
        ("RUCKUS One API", ("api_base_url", "ruckus_tenant_id", "client_id")),
        ("Defaults", ("default_site_group", "default_device_role", "default_manufacturer")),
        ("Venue Mapping", ("venue_mapping_mode", "venue_locations_parent_site", "venue_child_location_name")),
        ("Venue Selection", ("venues_selected",)),
        ("Stub Objects", ("allow_stub_devices", "allow_stub_vlans", "allow_stub_wireless")),
        ("Sync Toggles", ("sync_wlans", "sync_aps", "sync_switches", "sync_interfaces", "sync_wifi_clients", "sync_wired_clients", "sync_cabling", "sync_wireless_links", "sync_vlans")),
        ("Authoritative", ("authoritative_devices", "authoritative_interfaces", "authoritative_ips", "authoritative_vlans", "authoritative_wireless", "authoritative_cabling")),
        ("Status", ("last_sync", "last_sync_status", "last_sync_message")),
    )


class RuckusR1TenantConfigEditView(generic.ObjectEditView):
    queryset = RuckusR1TenantConfig.objects.all()
    form = RuckusR1TenantConfigForm


class RuckusR1TenantConfigDeleteView(generic.ObjectDeleteView):
    queryset = RuckusR1TenantConfig.objects.all()


class RuckusR1TenantConfigRunView(View):
    def post(self, request, pk):
        cfg = get_object_or_404(RuckusR1TenantConfig, pk=pk)
        try:
            msg = run_sync_for_tenantconfig(cfg)
            messages.success(request, msg)
        except Exception as e:
            messages.error(request, f"Sync failed: {e}")
        return redirect("plugins:ruckus_r1_sync:ruckusr1tenantconfig", pk=pk)


class RuckusR1TenantConfigRefreshVenuesView(View):
    def post(self, request, pk):
        cfg = get_object_or_404(RuckusR1TenantConfig, pk=pk)
        try:
            api = _make_client(cfg)
            venues = _query_all(api, "/venues/query", {"limit": 500})
            cache = []
            for v in venues:
                if not isinstance(v, dict):
                    continue
                vid = (v.get("id") or v.get("venueId") or "").strip()
                name = (v.get("name") or v.get("venueName") or vid or "").strip()
                if not vid:
                    continue
                cache.append({"id": vid, "name": name})
            cache.sort(key=lambda x: ((x.get("name") or "").lower(), x.get("id") or ""))
            cfg.venues_cache = cache
            cfg.save()
            messages.success(request, f"Venues refreshed: {len(cache)} found.")
        except Exception as e:
            messages.error(request, f"Refresh venues failed: {e}")
        return redirect("plugins:ruckus_r1_sync:ruckusr1tenantconfig", pk=pk)


class RuckusR1SyncLogListView(generic.ObjectListView):
    queryset = RuckusR1SyncLog.objects.all()
    table = RuckusR1SyncLogTable
    actions = ()


class RuckusR1ClientListView(generic.ObjectListView):
    queryset = RuckusR1Client.objects.all()
    table = RuckusR1ClientTable
    actions = ()
