from tenancy.models import Tenant
from .sync import run_sync_for_tenant

def sync_tenant(tenant_id: int):
    tenant = Tenant.objects.get(id=tenant_id)
    return run_sync_for_tenant(tenant)
 