"""Tenant add-on entitlement helpers."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from core.models import TenantAddon


def tenant_has_addon(tenant_id, addon_code: str) -> bool:
    if not tenant_id:
        return False
    return TenantAddon.objects.filter(
        tenant_id=tenant_id,
        addon_code=addon_code,
        enabled=True,
    ).exists()


class RequiresTenantAddon(BasePermission):
    """Authenticated tenant user with a specific add-on enabled."""

    message = 'This feature requires an active add-on subscription.'

    def __init__(self, addon_code: str):
        self.addon_code = addon_code

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id and request.user.tenant_id:
            tenant_id = request.user.tenant_id
            request.tenant_id = tenant_id
        if request.user.is_superuser:
            return True
        return tenant_has_addon(tenant_id, self.addon_code)
