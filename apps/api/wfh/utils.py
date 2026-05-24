from employees.models import Employee
from wfh.models import TrackerAuditLog

WFH_HR_PERMISSIONS = ("wfh.approve.hr", "wfh.view.all")
WFH_POLICY_PERMISSIONS = ("wfh.policy.manage", "wfh.admin.settings")


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_employee_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return Employee.objects.filter(user=user).select_related("tenant", "reporting_manager").first()


def resolve_tenant_id(user):
    """Tenant for HRMS API scoping: Employee profile first, then User.tenant."""
    if not user or not user.is_authenticated:
        return None
    employee = get_employee_for_user(user)
    if employee:
        return employee.tenant_id
    return getattr(user, "tenant_id", None)


def user_has_wfh_permission(user, *codes):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not codes:
        return True
    return user.role_mappings.filter(role__permissions__code__in=codes).exists()


def is_hr_wfh_viewer(user):
    return user_has_wfh_permission(user, *WFH_HR_PERMISSIONS)


def audit_log(request, action, entity_type="", entity_id="", metadata=None):
    tenant_id = resolve_tenant_id(request.user) if request.user.is_authenticated else None
    TrackerAuditLog.objects.create(
        tenant_id=tenant_id,
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else "",
        metadata=metadata or {},
        ip_address=get_client_ip(request),
    )
