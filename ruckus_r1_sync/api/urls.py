from . import router
from .views import RuckusR1TenantConfigViewSet

router.register("tenant-configs", RuckusR1TenantConfigViewSet)

urlpatterns = router.urls
 