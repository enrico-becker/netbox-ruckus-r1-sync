from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from netbox.views import generic

from .forms import RuckusR1TenantConfigForm
from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client
from .tables import RuckusR1TenantConfigTable, RuckusR1SyncLogTable, RuckusR1ClientTable
from .sync import run_sync_for_tenantconfig


class RuckusR1TenantConfigListView(generic.ObjectListView):
    queryset = RuckusR1TenantConfig.objects.all()
    table = RuckusR1TenantConfigTable


class RuckusR1TenantConfigView(generic.ObjectView):
    queryset = RuckusR1TenantConfig.objects.all()
    object_fields = (
        ("General", (
            "tenant",
            "name",
            "enabled",
        )),
        ("Ruckus API", (
            "api_base_url",
            "ruckus_tenant_id",
            "client_id",
        )),
        ("Sync Options", (
            "authoritative_devices",
            "authoritative_interfaces",
            "authoritative_vlans",
            "authoritative_wireless",
            "authoritative_cabling",
        )),
        ("Status", (
            "last_sync",
            "last_sync_status",
            "last_sync_message",
        )),
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


class RuckusR1SyncLogListView(generic.ObjectListView):
    queryset = RuckusR1SyncLog.objects.all()
    table = RuckusR1SyncLogTable
    actions = ()


class RuckusR1ClientListView(generic.ObjectListView):
    queryset = RuckusR1Client.objects.all()
    table = RuckusR1ClientTable
    actions = ()
