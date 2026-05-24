from django.urls import path
from .views import (
    HRDashboardView,
    ManagerDashboardView,
    CompanyDashboardView,
    EmployeeDashboardView,
    PayrollDashboardView,
    FinanceDashboardView,
    ITDashboardView,
    RecruitmentDashboardView,
    AuditDashboardView,
)

urlpatterns = [
    path('hr/', HRDashboardView.as_view(), name='dashboard-hr'),
    path('manager/', ManagerDashboardView.as_view(), name='dashboard-manager'),
    path('company/', CompanyDashboardView.as_view(), name='dashboard-company'),
    path('employee/', EmployeeDashboardView.as_view(), name='dashboard-employee'),
    path('payroll/', PayrollDashboardView.as_view(), name='dashboard-payroll'),
    path('finance/', FinanceDashboardView.as_view(), name='dashboard-finance'),
    path('it/', ITDashboardView.as_view(), name='dashboard-it'),
    path('recruitment/', RecruitmentDashboardView.as_view(), name='dashboard-recruitment'),
    path('audit/', AuditDashboardView.as_view(), name='dashboard-audit'),
]
