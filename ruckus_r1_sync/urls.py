from __future__ import annotations

from django.urls import path
from . import views

app_name = "ruckus_r1_sync"

urlpatterns = [
    path("configs/", views.RuckusR1TenantConfigListView.as_view(), name="ruckusr1tenantconfig_list"),
    path("configs/add/", views.RuckusR1TenantConfigEditView.as_view(), name="ruckusr1tenantconfig_add"),
    path("configs/<int:pk>/", views.RuckusR1TenantConfigView.as_view(), name="ruckusr1tenantconfig"),
    path("configs/<int:pk>/edit/", views.RuckusR1TenantConfigEditView.as_view(), name="ruckusr1tenantconfig_edit"),
    path("configs/<int:pk>/delete/", views.RuckusR1TenantConfigDeleteView.as_view(), name="ruckusr1tenantconfig_delete"),

    path("logs/", views.RuckusR1SyncLogListView.as_view(), name="ruckusr1synclog_list"),
    path("clients/", views.RuckusR1ClientListView.as_view(), name="ruckusr1client_list"),
]
 