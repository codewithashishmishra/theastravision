from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedTenantUser
from core.tenant_utils import attach_tenant_to_request, get_employee_for_user, resolve_tenant_id

from assets.models import Asset
from .kpi import base_kpis, payroll_kpis, finance_kpis, manager_kpis, employee_kpis


class BaseDashboardView(APIView):
    permission_classes = [IsAuthenticatedTenantUser]

    def get_kpis(self, request):
        attach_tenant_to_request(request)
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return None
        return tenant_id

    def get(self, request):
        tenant_id = self.get_kpis(request)
        if not tenant_id:
            return Response({'detail': 'Tenant required.'}, status=403)
        return Response(self.build_payload(tenant_id, request))

    def build_payload(self, tenant_id, request):
        raise NotImplementedError


class HRDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        data = base_kpis(tenant_id)
        data['dashboard'] = 'hr'
        return data


class ManagerDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        employee = get_employee_for_user(request.user)
        data = manager_kpis(tenant_id, employee.id if employee else None)
        data['dashboard'] = 'manager'
        return data


class CompanyDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        data = base_kpis(tenant_id)
        data['dashboard'] = 'company'
        return data


class EmployeeDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        employee = get_employee_for_user(request.user)
        data = employee_kpis(tenant_id, employee.id if employee else None)
        data['dashboard'] = 'employee'
        return data


class PayrollDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        data = payroll_kpis(tenant_id)
        data['dashboard'] = 'payroll'
        return data


class FinanceDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        data = finance_kpis(tenant_id)
        data['dashboard'] = 'finance'
        return data


class ITDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        data = base_kpis(tenant_id)
        data.update({
            'assets_total': Asset.objects.filter(tenant_id=tenant_id).count(),
            'assets_available': Asset.objects.filter(tenant_id=tenant_id, status='Available').count(),
            'open_tickets_high': Ticket.objects.filter(
                tenant_id=tenant_id, status='Open', priority='High'
            ).count(),
        })
        data['dashboard'] = 'it'
        return data


class RecruitmentDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        from recruitment.models import Interview

        data = base_kpis(tenant_id)
        data.update({
            'interviews_upcoming': Interview.objects.filter(
                tenant_id=tenant_id,
                scheduled_at__gte=timezone.now(),
            ).count(),
            'interviews_total': Interview.objects.filter(tenant_id=tenant_id).count(),
        })
        data['dashboard'] = 'recruitment'
        return data


class AuditDashboardView(BaseDashboardView):
    def build_payload(self, tenant_id, request):
        data = base_kpis(tenant_id)
        data['dashboard'] = 'audit'
        return data
