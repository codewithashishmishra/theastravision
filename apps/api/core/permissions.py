from rest_framework.permissions import BasePermission

from core.tenant_utils import resolve_tenant_id


class IsAuthenticatedTenantUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant_id = resolve_tenant_id(request.user)
        if tenant_id:
            request.tenant_id = tenant_id
            return True
        return request.user.is_superuser


def require_permission(*permissions):
    """
    Returns a permission class that checks if the user has any of the specified permissions.
    """
    class RequirePermission(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            if request.user.is_superuser:
                return True
            return request.user.role_mappings.filter(role__permissions__code__in=permissions).exists()
    
    return RequirePermission

class IsSuperAdmin(BasePermission):
    """Platform super admins: Django superuser or Super Admin role."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.role_mappings.filter(role__name='Super Admin').exists()


TENANT_IAM_ROLE_NAMES = ('Super Admin', 'Company Admin', 'IT Admin')


class IsTenantIamAdmin(BasePermission):
    """Platform or tenant IAM administrators."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.role_mappings.filter(
            role__name__in=TENANT_IAM_ROLE_NAMES
        ).exists()
