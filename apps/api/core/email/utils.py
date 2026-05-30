"""Shared email helpers."""

from core.models import Tenant
from core.tenant_utils import resolve_tenant_id


def resolve_platform_tenant_id(campaign=None):
    if campaign and getattr(campaign, 'created_by_id', None):
        tid = resolve_tenant_id(campaign.created_by)
        if tid:
            return tid
    tenant = Tenant.objects.order_by('created_at').first()
    return tenant.id if tenant else None
