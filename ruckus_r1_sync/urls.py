from __future__ import annotations

from django.urls import path
from netbox.views.generic import ObjectChangeLogView

from . import views
from .models import RuckusR1TenantConfig

app_name = "ruckus_r1_sync"

urlpatterns = [
    path("configs/", views.RuckusR1TenantConfigListView.as_view(), name="ruckusr1tenantconfig_list"),
    path("configs/add/", views.RuckusR1TenantConfigEditView.as_view(), name="ruckusr1tenantconfig_add"),
    path("configs/<int:pk>/", views.RuckusR1TenantConfigView.as_view(), name="ruckusr1tenantconfig"),
    path("configs/<int:pk>/edit/", views.RuckusR1TenantConfigEditView.as_view(), name="ruckusr1tenantconfig_edit"),
    path("configs/<int:pk>/delete/", views.RuckusR1TenantConfigDeleteView.as_view(), name="ruckusr1tenantconfig_delete"),

    path(
        "configs/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        {"model": RuckusR1TenantConfig},
        name="ruckusr1tenantconfig_changelog",
    ),

    path("configs/<int:pk>/run/", views.RuckusR1TenantConfigRunView.as_view(), name="ruckusr1tenantconfig_run"),
    path("configs/<int:pk>/refresh-venues/", views.RuckusR1TenantConfigRefreshVenuesView.as_view(), name="ruckusr1tenantconfig_refresh_venues"),

    path("logs/", views.RuckusR1SyncLogListView.as_view(), name="ruckusr1synclog_list"),
    path("clients/", views.RuckusR1ClientListView.as_view(), name="ruckusr1client_list"),
]
