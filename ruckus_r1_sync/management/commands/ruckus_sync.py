from django.core.management.base import BaseCommand, CommandError

from tenancy.models import Tenant

from ruckus_r1_sync.models import RuckusR1TenantConfig
from ruckus_r1_sync.sync import run_sync_for_tenantconfig


class Command(BaseCommand):
    help = "Run RUCKUS R1 sync for a given NetBox tenant (by tenant-id) or for all enabled configs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            type=int,
            dest="tenant_id",
            help="NetBox tenant ID (tenancy_tenant.id) for which to run the sync",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            dest="all_configs",
            help="Run sync for all enabled tenant configs",
        )

    def handle(self, *args, **options):
        tenant_id = options.get("tenant_id")
        all_configs = options.get("all_configs")

        try:
            if all_configs:
                configs = RuckusR1TenantConfig.objects.filter(enabled=True).order_by("id")
                if not configs.exists():
                    self.stdout.write(self.style.WARNING("No enabled tenant configs found."))
                    return

                for cfg in configs:
                    self.stdout.write(f"Running sync for config #{cfg.pk} (tenant={cfg.tenant_id}, name={cfg.name})")
                    run_sync_for_tenantconfig(cfg.pk)

                self.stdout.write(self.style.SUCCESS(f"Done. Synced {configs.count()} configs."))
                return

            if not tenant_id:
                raise CommandError("Provide either --tenant-id <id> or --all")

            tenant = Tenant.objects.filter(id=tenant_id).first()
            if not tenant:
                raise CommandError(f"Tenant with id={tenant_id} not found.")

            cfg = RuckusR1TenantConfig.objects.filter(tenant=tenant).first()
            if not cfg:
                raise CommandError(f"No RuckusR1TenantConfig found for tenant id={tenant_id}")

            if not cfg.enabled:
                self.stdout.write(self.style.WARNING(f"Config #{cfg.pk} for tenant {tenant_id} is disabled."))
                return

            self.stdout.write(f"Running sync for config #{cfg.pk} (tenant={tenant_id}, name={cfg.name})")
            run_sync_for_tenantconfig(cfg.pk)
            self.stdout.write(self.style.SUCCESS("Sync finished successfully."))

        except Exception as e:
            raise CommandError(f"Sync failed: {e}") from e
 