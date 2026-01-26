from __future__ import annotations

from netbox.views import generic

from .forms import RuckusR1TenantConfigForm
from .models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client
from .tables import RuckusR1TenantConfigTable, RuckusR1SyncLogTable, RuckusR1ClientTable


class RuckusR1TenantConfigListView(generic.ObjectListView):
    queryset = RuckusR1TenantConfig.objects.all()
    table = RuckusR1TenantConfigTable




class RuckusR1TenantConfigView(generic.ObjectView):
    queryset = RuckusR1TenantConfig.objects.all()


class RuckusR1TenantConfigEditView(generic.ObjectEditView):
    queryset = RuckusR1TenantConfig.objects.all()
    form = RuckusR1TenantConfigForm


class RuckusR1TenantConfigDeleteView(generic.ObjectDeleteView):
    queryset = RuckusR1TenantConfig.objects.all()


class RuckusR1SyncLogListView(generic.ObjectListView):
    queryset = RuckusR1SyncLog.objects.all()
    table = RuckusR1SyncLogTable
    # KEY: disable UI actions that could imply edit/delete
    actions = ()


class RuckusR1ClientListView(generic.ObjectListView):
    queryset = RuckusR1Client.objects.all()
    table = RuckusR1ClientTable
    # KEY: disable UI actions that could imply edit/delete
    actions = ()
 