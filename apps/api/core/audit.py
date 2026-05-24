"""Platform-wide compliance audit logging (SystemAuditLog)."""

from core.models import SystemAuditLog, Tenant
from core.tenant_utils import resolve_tenant_id
from core.utils import get_client_ip


def _resolve_tenant(tenant):
    if tenant is None:
        return None
    if isinstance(tenant, Tenant):
        return tenant
    return Tenant.objects.filter(id=tenant).first()


def system_audit_log(
    request=None,
    *,
    action,
    module,
    metadata=None,
    tenant=None,
    user=None,
    ip_address=None,
):
    ip = ip_address
    actor = user
    tenant_obj = _resolve_tenant(tenant)

    if request is not None:
        if ip is None:
            ip = get_client_ip(request)
        if actor is None and getattr(request, "user", None) and request.user.is_authenticated:
            actor = request.user
        if tenant_obj is None and getattr(request, "user", None) and request.user.is_authenticated:
            tenant_id = resolve_tenant_id(request.user)
            if tenant_id:
                tenant_obj = Tenant.objects.filter(id=tenant_id).first()

    SystemAuditLog.objects.create(
        tenant=tenant_obj,
        user=actor if getattr(actor, "is_authenticated", True) else None,
        action=action,
        module=module,
        ip_address=ip,
        metadata=metadata or {},
    )


class AuditViewSetMixin:
    """Mixin for DRF viewsets — logs create/update/destroy to SystemAuditLog."""

    audit_module = "iam"
    audit_resource = "resource"

    def perform_create(self, serializer):
        super().perform_create(serializer)
        system_audit_log(
            self.request,
            action=f"{self.audit_resource}.create",
            module=self.audit_module,
            metadata={"id": str(serializer.instance.pk)},
        )

    def perform_update(self, serializer):
        super().perform_update(serializer)
        system_audit_log(
            self.request,
            action=f"{self.audit_resource}.update",
            module=self.audit_module,
            metadata={"id": str(serializer.instance.pk)},
        )

    def perform_destroy(self, instance):
        pk = str(instance.pk)
        super().perform_destroy(instance)
        system_audit_log(
            self.request,
            action=f"{self.audit_resource}.delete",
            module=self.audit_module,
            metadata={"id": pk},
        )
