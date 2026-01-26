from netbox.api.viewsets import NetBoxModelViewSet
from ..models import RuckusR1TenantConfig
from .serializers import RuckusR1TenantConfigSerializer


class RuckusR1TenantConfigViewSet(NetBoxModelViewSet):
    queryset = RuckusR1TenantConfig.objects.all()
    serializer_class = RuckusR1TenantConfigSerializer
 