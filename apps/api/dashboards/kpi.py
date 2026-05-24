from django.db.models import Q, Sum
from django.utils import timezone

from attendance.models import AttendanceLog, AttendanceRegularization
from employees.models import Employee
from expenses.models import ExpenseClaim
from helpdesk.models import Ticket
from leave.models import LeaveRequest
from offboarding.models import Resignation
from payroll.models import PayrollRun, Payslip
from recruitment.models import Candidate, JobRequisition
from wfh.models import WFHRequest


def base_kpis(tenant_id):
    today = timezone.now().date()
    return {
        'employee_count': Employee.objects.filter(tenant_id=tenant_id, status='Active').count(),
        'leave_pending': LeaveRequest.objects.filter(tenant_id=tenant_id, status='Pending').count(),
        'attendance_today': AttendanceLog.objects.filter(tenant_id=tenant_id, date=today).count(),
        'regularization_pending': AttendanceRegularization.objects.filter(
            tenant_id=tenant_id, status='Pending'
        ).count(),
        'open_tickets': Ticket.objects.filter(tenant_id=tenant_id, status='Open').count(),
        'expense_pending': ExpenseClaim.objects.filter(tenant_id=tenant_id, status='Pending').count(),
        'wfh_pending': WFHRequest.objects.filter(tenant_id=tenant_id, status='pending').count(),
        'open_requisitions': JobRequisition.objects.filter(tenant_id=tenant_id, status='Open').count(),
        'candidates_in_pipeline': Candidate.objects.filter(
            tenant_id=tenant_id
        ).exclude(stage__in=['Hired', 'Rejected']).count(),
        'resignations_pending': Resignation.objects.filter(tenant_id=tenant_id, status='Pending').count(),
    }


def payroll_kpis(tenant_id):
    kpis = base_kpis(tenant_id)
    kpis.update({
        'payroll_runs_draft': PayrollRun.objects.filter(tenant_id=tenant_id, status='Draft').count(),
        'payslips_unreleased': Payslip.objects.filter(
            tenant_id=tenant_id, is_released=False
        ).count(),
        'payroll_total_net': Payslip.objects.filter(tenant_id=tenant_id).aggregate(
            total=Sum('net_pay')
        )['total'] or 0,
    })
    return kpis


def finance_kpis(tenant_id):
    kpis = base_kpis(tenant_id)
    agg = ExpenseClaim.objects.filter(tenant_id=tenant_id).aggregate(
        pending_amount=Sum('amount', filter=Q(status='Pending')),
        approved_amount=Sum('amount', filter=Q(status='Approved')),
    )
    kpis.update({
        'expense_pending_amount': agg['pending_amount'] or 0,
        'expense_approved_amount': agg['approved_amount'] or 0,
    })
    return kpis


def manager_kpis(tenant_id, manager_employee_id):
    kpis = base_kpis(tenant_id)
    if manager_employee_id:
        reportee_ids = Employee.objects.filter(
            tenant_id=tenant_id, reporting_manager_id=manager_employee_id
        ).values_list('id', flat=True)
        kpis.update({
            'team_size': len(reportee_ids),
            'team_leave_pending': LeaveRequest.objects.filter(
                employee_id__in=reportee_ids, status='Pending'
            ).count(),
            'team_expense_pending': ExpenseClaim.objects.filter(
                employee_id__in=reportee_ids, status='Pending'
            ).count(),
        })
    return kpis


def employee_kpis(tenant_id, employee_id):
    today = timezone.now().date()
    kpis = {
        'my_leave_pending': 0,
        'my_attendance_today': False,
        'my_open_tickets': 0,
        'my_expense_pending': 0,
    }
    if employee_id:
        kpis['my_leave_pending'] = LeaveRequest.objects.filter(
            tenant_id=tenant_id, employee_id=employee_id, status='Pending'
        ).count()
        kpis['my_attendance_today'] = AttendanceLog.objects.filter(
            tenant_id=tenant_id, employee_id=employee_id, date=today
        ).exists()
        kpis['my_open_tickets'] = Ticket.objects.filter(
            tenant_id=tenant_id, employee_id=employee_id, status='Open'
        ).count()
        kpis['my_expense_pending'] = ExpenseClaim.objects.filter(
            tenant_id=tenant_id, employee_id=employee_id, status='Pending'
        ).count()
    return kpis
