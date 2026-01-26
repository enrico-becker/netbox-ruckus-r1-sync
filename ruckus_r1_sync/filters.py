import django_filters

from .models import RuckusR1SyncLog, RuckusR1TenantConfig


class SyncLogFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    tenant = django_filters.CharFilter(field_name="tenant__name", lookup_expr="icontains")

    class Meta:
        model = RuckusR1SyncLog
        fields = ["status", "tenant"]


class TenantConfigFilterSet(django_filters.FilterSet):
    tenant = django_filters.CharFilter(field_name="tenant__name", lookup_expr="icontains")
    enabled = django_filters.BooleanFilter()

    class Meta:
        model = RuckusR1TenantConfig
        fields = ["tenant", "enabled"]
 