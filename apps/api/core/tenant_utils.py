"""Shared tenant and employee resolution for HRMS APIs."""
from employees.models import Employee


def get_employee_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return Employee.objects.filter(user=user).select_related("tenant", "reporting_manager", "branch").first()


def resolve_tenant_id(user):
    if not user or not user.is_authenticated:
        return None
    employee = get_employee_for_user(user)
    if employee:
        return employee.tenant_id
    return getattr(user, "tenant_id", None)


def attach_tenant_to_request(request):
    tenant_id = resolve_tenant_id(request.user)
    request.tenant_id = tenant_id
    return tenant_id


def resolve_request_tenant_id(request):
    """Tenant for the current request: user/employee tenant, or superuser ?tenant_id= override."""
    tenant_id = getattr(request, 'tenant_id', None) or resolve_tenant_id(request.user)
    if tenant_id:
        return tenant_id
    if not request.user.is_authenticated or not request.user.is_superuser:
        return None
    raw = request.query_params.get('tenant_id')
    if not raw:
        return None
    try:
        import uuid
        from core.models import Tenant

        tid = uuid.UUID(str(raw))
    except (ValueError, AttributeError):
        return None
    if Tenant.objects.filter(id=tid).exists():
        from core.audit import system_audit_log

        system_audit_log(
            request,
            action="tenant.override",
            module="iam",
            user=request.user,
            metadata={"tenant_id": str(tid)},
        )
        return tid
    return None
