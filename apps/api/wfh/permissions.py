from rest_framework.permissions import BasePermission

from wfh.models import EmployeeConsent, WFHRequest
from wfh.services.session import get_active_session, get_approved_wfh_for_today
from wfh.utils import get_employee_for_user


class IsEmployeeUser(BasePermission):
    def has_permission(self, request, view):
        return get_employee_for_user(request.user) is not None


class HasActiveApprovedWFH(BasePermission):
    def has_permission(self, request, view):
        employee = get_employee_for_user(request.user)
        if not employee:
            return False
        return get_approved_wfh_for_today(employee) is not None


class HasRecordedConsent(BasePermission):
    def has_permission(self, request, view):
        employee = get_employee_for_user(request.user)
        if not employee:
            return False
        return EmployeeConsent.objects.filter(
            employee=employee,
            consent_type="wfh_tracking_v1",
            revoked_at__isnull=True,
        ).exists()


class HasActiveWorkSession(BasePermission):
    def has_permission(self, request, view):
        employee = get_employee_for_user(request.user)
        if not employee:
            return False
        return get_active_session(employee) is not None


class CanViewEmployeeTracking(BasePermission):
    """Manager sees reportees; HR/Admin see tenant."""

    def has_object_permission(self, request, view, obj):
        viewer_emp = get_employee_for_user(request.user)
        if request.user.is_superuser:
            return True
        target_employee = getattr(obj, "employee", obj)
        if not viewer_emp:
            return request.user.role_mappings.filter(
                role__permissions__code__in=["wfh.view.all", "wfh.approve.hr"]
            ).exists()
        if viewer_emp.id == target_employee.id:
            return True
        if target_employee.reporting_manager_id == viewer_emp.id:
            return True
        return request.user.role_mappings.filter(
            role__permissions__code__in=["wfh.view.all", "wfh.approve.hr"]
        ).exists()
