"""ruckus_r1_sync.jobs (System-job only, compatible with your NetBox build)

Your NetBox build treats `netbox.jobs.Job` as a Django model (hence Django Meta validation errors).
So plugin-defined UI Jobs are not supported via subclassing Job here.

What *does* work (as you already saw in the registry) is `JobRunner` + `@system_job(interval=<minutes>)`.

This file registers ONE system job:
- RUCKUS One Sync (all enabled)  -> runs every <interval> minutes (default 15) and syncs all enabled configs.

It also implements 'stop after N failures' (default 3) per config:
- counter stored in RuckusR1TenantConfig.custom_field_data['sync_failures']
- after N failures -> cfg.enabled=False

If you need per-config cron times, use NetBox Scheduled Jobs only if your build exposes that UI.
Otherwise: run multiple external cron entries calling your management command with a config ID.
"""

from __future__ import annotations

from typing import Any, Dict

from django.db import transaction

from netbox.jobs import JobRunner, system_job

from .models import RuckusR1TenantConfig
from .sync import run_sync_for_tenantconfig

FAIL_KEY = "sync_failures"
FAIL_LIMIT_DEFAULT = 3

# Adjust this to your needs (minutes). 15 is a practical default.
DEFAULT_INTERVAL_MINUTES = 15


def _get_failures(cfg: RuckusR1TenantConfig) -> int:
    data = cfg.custom_field_data or {}
    try:
        return int(data.get(FAIL_KEY, 0) or 0)
    except Exception:
        return 0


def _set_failures(cfg: RuckusR1TenantConfig, n: int) -> None:
    data = dict(cfg.custom_field_data or {})
    data[FAIL_KEY] = int(n)
    cfg.custom_field_data = data


def _record_success(cfg: RuckusR1TenantConfig) -> None:
    with transaction.atomic():
        cfg.refresh_from_db()
        _set_failures(cfg, 0)
        cfg.save(update_fields=["custom_field_data", "last_updated"])


def _record_failure(cfg: RuckusR1TenantConfig, stop_after_failures: int) -> int:
    with transaction.atomic():
        cfg.refresh_from_db()
        failures = _get_failures(cfg) + 1
        _set_failures(cfg, failures)
        if failures >= int(stop_after_failures):
            cfg.enabled = False
        cfg.save(update_fields=["custom_field_data", "enabled", "last_updated"])
        return failures

DEFAULT_INTERVAL_MINUTES = 1
@system_job(interval=DEFAULT_INTERVAL_MINUTES)
class RuckusSyncAllEnabled(JobRunner):
    """RUCKUS One Sync (all enabled) - System Job"""

    class Meta:
        name = "RUCKUS One Sync (all enabled)"

    def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self.logger.warning("RUCKUS SYSTEM JOB RUNNING")
        stop_after_failures = int(kwargs.get("stop_after_failures", FAIL_LIMIT_DEFAULT))

        ok = 0
        fail = 0
        skipped = 0

        for cfg in RuckusR1TenantConfig.objects.order_by("id"):
            if not cfg.enabled:
                skipped += 1
                continue

            try:
                run_sync_for_tenantconfig(cfg)
                _record_success(cfg)
                ok += 1
            except Exception as e:
                failures = _record_failure(cfg, stop_after_failures)
                self.logger.error(
                    "Sync failed for TenantConfig id=%s (failures=%s/%s): %s",
                    cfg.pk, failures, stop_after_failures, e,
                )
                fail += 1

        return {"ok": ok, "fail": fail, "skipped": skipped}
