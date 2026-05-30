from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import Tenant, User
from employees.models import Employee
from organization.models import Department
from wfh.models import EmployeeConsent, ProductivityRule, WFHPolicy, WFHRequest
from wfh.services.approval import hr_approve, manager_approve
from wfh.services.productivity import classify_focus
from wfh.services.session import get_approved_wfh_for_today


class WFHApprovalTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Co", domain="testco")
        WFHPolicy.objects.create(tenant=self.tenant, require_hr_approval=True, is_active=True)
        self.user = User.objects.create_user(
            username="emp@test.com", email="emp@test.com", password="pass", tenant=self.tenant
        )
        self.manager_user = User.objects.create_user(
            username="mgr@test.com", email="mgr@test.com", password="pass", tenant=self.tenant
        )
        dept = Department.objects.create(tenant=self.tenant, name="Eng", code="ENG")
        self.manager = Employee.objects.create(
            tenant=self.tenant,
            user=self.manager_user,
            employee_code="M001",
            first_name="Mgr",
            last_name="One",
            date_of_joining=date.today(),
            department=dept,
        )
        self.employee = Employee.objects.create(
            tenant=self.tenant,
            user=self.user,
            employee_code="E001",
            first_name="Emp",
            last_name="One",
            date_of_joining=date.today(),
            reporting_manager=self.manager,
            department=dept,
        )
        self.request = WFHRequest.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            reason="WFH",
        )

    def test_manager_approve_requires_hr(self):
        manager_approve(self.request, self.manager_user)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, WFHRequest.STATUS_MANAGER_APPROVED)
        self.assertFalse(self.request.is_wfh_approved)

    def test_full_approval_flow(self):
        manager_approve(self.request, self.manager_user)
        hr_approve(self.request, self.manager_user)
        self.request.refresh_from_db()
        self.assertTrue(self.request.is_wfh_approved)
        self.assertIsNotNone(get_approved_wfh_for_today(self.employee))

    def test_consent_model(self):
        EmployeeConsent.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            consent_type="wfh_tracking_v1",
        )
        self.assertTrue(
            EmployeeConsent.objects.filter(employee=self.employee, revoked_at__isnull=True).exists()
        )


class ProductivityRuleTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Prod Co", domain="prodco")

    def test_exact_rule_classification(self):
        rule = ProductivityRule.objects.create(
            tenant=self.tenant,
            name="VSCode",
            target_type=ProductivityRule.TARGET_APP,
            match_type=ProductivityRule.MATCH_EXACT,
            pattern="code",
            is_productive=True,
        )
        is_productive, matched = classify_focus(self.tenant.id, "code", "project")
        self.assertTrue(is_productive)
        self.assertEqual(matched.id, rule.id)

    def test_unmatched_defaults_to_unproductive(self):
        is_productive, matched = classify_focus(self.tenant.id, "spotify", "music")
        self.assertFalse(is_productive)
        self.assertIsNone(matched)
