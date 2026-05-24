"""Shared tenant and employee resolution for HRMS APIs."""
from employees.models import Employee


def get_employee_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return Employee.objects.filter(user=user).select_related("tenant", "reporting_manager").first()


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
