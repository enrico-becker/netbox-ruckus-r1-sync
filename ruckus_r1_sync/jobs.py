# plugins/netbox-ruckus-r1-sync/ruckus_r1_sync/jobs.py
from netbox.jobs import Job

from .models import TenantConfig
from .sync import run_sync_for_tenantconfig


class RuckusFullSyncJob(Job):
    class Meta:
        name = "RUCKUS One Full Sync"

    def run(self, *args, **kwargs):
        ok = 0
        fail = 0
        for cfg in TenantConfig.objects.all():
            try:
                run_sync_for_tenantconfig(cfg)
                ok += 1
            except Exception:
                fail += 1
        return {"ok": ok, "fail": fail}
 