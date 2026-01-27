from . import router
from .views import RuckusR1TenantConfigViewSet, RuckusR1SyncLogViewSet, RuckusR1ClientViewSet

router.register("tenant-configs", RuckusR1TenantConfigViewSet)
router.register("sync-logs", RuckusR1SyncLogViewSet)
router.register("clients", RuckusR1ClientViewSet)

urlpatterns = router.urls
