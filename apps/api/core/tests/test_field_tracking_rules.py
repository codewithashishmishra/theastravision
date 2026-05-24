from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from attendance.models import AttendanceSettings
from attendance.services.office_hours import is_within_office_hours
from attendance.services.rules import resolve_attendance_rules, validate_not_near_home
from core.models import Tenant
from employees.models import Employee, EmployeeType, EmployeeWorkLocation


class FieldTrackingRulesTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Tenant A', domain='tenant-a', email_domain='a.com')
        self.employee_type = EmployeeType.objects.create(
            tenant=self.tenant,
            code='FIELD',
            name='Field',
            require_selfie_on_punch=True,
            require_gps_on_punch=True,
            enable_live_tracking=True,
            block_punch_near_home=True,
            require_home_location=True,
            allow_remote_punch=True,
        )
        self.employee = Employee.objects.create(
            tenant=self.tenant,
            employee_code='EMP100',
            first_name='Field',
            last_name='Agent',
            date_of_joining=timezone.localdate(),
            employee_type=self.employee_type,
        )

    def test_rules_merge_employee_type_flags(self):
        AttendanceSettings.objects.create(
            tenant=self.tenant,
            require_selfie=False,
            require_gps=False,
            allow_web_punch=True,
            allow_regularization=True,
        )
        rules = resolve_attendance_rules(self.employee)
        self.assertTrue(rules.require_selfie)
        self.assertTrue(rules.require_gps)
        self.assertTrue(rules.enable_live_tracking)
        self.assertTrue(rules.require_home_location)

    def test_block_punch_near_home(self):
        EmployeeWorkLocation.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            home_address='Test Home',
            home_latitude=Decimal('12.971600'),
            home_longitude=Decimal('77.594600'),
            completed_at=timezone.now(),
        )
        rules = resolve_attendance_rules(self.employee)
        ok, msg = validate_not_near_home(self.employee, Decimal('12.971650'), Decimal('77.594650'), rules)
        self.assertFalse(ok)
        self.assertIn('Punch blocked', msg)

    def test_office_hours_window(self):
        now = timezone.now()
        AttendanceSettings.objects.create(
            tenant=self.tenant,
            require_gps=True,
            require_selfie=False,
            allow_web_punch=True,
            allow_regularization=True,
            work_start_time=(now - timedelta(hours=1)).time(),
            work_end_time=(now + timedelta(hours=1)).time(),
            work_days=[now.isoweekday()],
            office_hours_timezone='UTC',
        )
        self.assertTrue(is_within_office_hours(self.tenant.id))
