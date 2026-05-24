from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import AttendanceSettings, GeoFence, Shift
from core.models import Tenant
from employees.models import Employee
from employees.services.employee_types import seed_employee_types_for_tenant, assign_default_employee_type
from expenses.models import ExpenseCategory, ExpensePolicy
from leave.models import LeaveType, LeavePolicy
from notifications.models import NotificationPreference
from onboarding.models import OnboardingChecklist, OnboardingTask
from organization.models import Branch, CompanyProfile


LEAVE_TYPES = [
    ('Annual Leave', 'AL', True),
    ('Sick Leave', 'SL', True),
    ('Casual Leave', 'CL', True),
    ('Unpaid Leave', 'UL', False),
]

EXPENSE_CATEGORIES = [
    ('Travel', 'TRAVEL'),
    ('Meals', 'MEALS'),
    ('Office Supplies', 'SUPPLIES'),
    ('Client Entertainment', 'CLIENT'),
]

ONBOARDING_TASKS = [
    ('IT laptop setup', 'IT', 1),
    ('HR orientation', 'HR', 2),
    ('Payroll bank details', 'HR', 3),
    ('Department intro', 'Manager', 4),
]


class Command(BaseCommand):
    help = 'Seed HRMS reference data per tenant (attendance, leave, expenses, onboarding, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Limit seeding to a single tenant UUID',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.all()
        if options.get('tenant_id'):
            tenants = tenants.filter(id=options['tenant_id'])

        if not tenants.exists():
            self.stdout.write(self.style.WARNING('No tenants found. Run seed_dev first.'))
            return

        for tenant in tenants[:50]:
            self._seed_tenant(tenant)

        self.stdout.write(self.style.SUCCESS('HRMS seed complete'))

    def _seed_tenant(self, tenant):
        profile = CompanyProfile.objects.filter(tenant=tenant).first()
        AttendanceSettings.objects.get_or_create(
            tenant=tenant,
            defaults={
                'company_profile': profile,
                'default_radius_meters': 100,
                'require_gps': True,
                'require_selfie': False,
                'allow_web_punch': True,
                'allow_regularization': True,
                'work_start_time': '09:00',
                'work_end_time': '18:00',
                'work_days': [1, 2, 3, 4, 5],
                'office_hours_timezone': 'UTC',
            },
        )
        seed_employee_types_for_tenant(tenant.id)

        Shift.objects.get_or_create(
            tenant=tenant,
            name='General Shift',
            defaults={
                'start_time': '09:00',
                'end_time': '18:00',
                'grace_period_mins': 15,
                'half_day_mins': 240,
                'is_default': True,
            },
        )

        for branch in Branch.objects.filter(tenant=tenant)[:3]:
            GeoFence.objects.get_or_create(
                tenant=tenant,
                branch=branch,
                defaults={
                    'latitude': Decimal('12.9716'),
                    'longitude': Decimal('77.5946'),
                    'radius_meters': 100,
                },
            )

        for name, code, is_paid in LEAVE_TYPES:
            lt, _ = LeaveType.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={'name': name, 'is_paid': is_paid},
            )
            LeavePolicy.objects.get_or_create(
                tenant=tenant,
                leave_type=lt,
                defaults={'annual_allowance': 12.0, 'accrual_frequency': 'Monthly'},
            )

        for name, code in EXPENSE_CATEGORIES:
            ExpenseCategory.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={'name': name},
            )

        ExpensePolicy.objects.get_or_create(
            tenant=tenant,
            name='Standard reimbursement',
            defaults={'max_amount': Decimal('50000.00')},
        )

        checklist, _ = OnboardingChecklist.objects.get_or_create(
            tenant=tenant,
            name='New hire checklist',
            defaults={'description': 'Default onboarding workflow'},
        )
        for title, department, sort_order in ONBOARDING_TASKS:
            OnboardingTask.objects.get_or_create(
                tenant=tenant,
                checklist=checklist,
                title=title,
                defaults={'department': department, 'sort_order': sort_order},
            )

        for emp in Employee.objects.filter(tenant=tenant).select_related('user')[:20]:
            assign_default_employee_type(emp)
            if emp.user_id:
                NotificationPreference.objects.get_or_create(
                    tenant=tenant,
                    user_id=emp.user_id,
                    defaults={
                        'email_enabled': True,
                        'sms_enabled': False,
                        'push_enabled': True,
                    },
                )

        self.stdout.write(f'Seeded HRMS data for tenant {tenant.name}')
