from netbox.api.viewsets import NetBoxModelViewSet

from ..models import RuckusR1TenantConfig, RuckusR1SyncLog, RuckusR1Client
from .serializers import (
    RuckusR1TenantConfigSerializer,
    RuckusR1SyncLogSerializer,
    RuckusR1ClientSerializer,
)


class RuckusR1TenantConfigViewSet(NetBoxModelViewSet):
    queryset = RuckusR1TenantConfig.objects.all()
    serializer_class = RuckusR1TenantConfigSerializer


class RuckusR1SyncLogViewSet(NetBoxModelViewSet):
    queryset = RuckusR1SyncLog.objects.all()
    serializer_class = RuckusR1SyncLogSerializer


class RuckusR1ClientViewSet(NetBoxModelViewSet):
    queryset = RuckusR1Client.objects.all()
    serializer_class = RuckusR1ClientSerializer
