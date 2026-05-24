from datetime import datetime, timezone as dt_timezone
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.jurisdictions import JURISDICTION_IN, JURISDICTION_US
from core.models import SystemAuditLog, Tenant, User
from core.timezone_utils import (
    activate_viewing_timezone,
    is_audit_path,
    is_valid_timezone,
    resolve_viewing_timezone,
)
from employees.models import Employee
from organization.models import Branch
from notifications.models import Notification


def _make_request(path="/api/v1/notifications/", ip="203.0.113.10"):
    factory = RequestFactory()
    request = factory.get(path)
    request.META["REMOTE_ADDR"] = ip
    return request


class TimezoneUtilsTests(TestCase):
    def test_is_audit_path(self):
        self.assertTrue(is_audit_path("/api/v1/audit/platform-logs/"))
        self.assertTrue(is_audit_path("/api/v1/wfh/admin/audit-logs/"))
        self.assertFalse(is_audit_path("/api/v1/notifications/"))

    def test_is_valid_timezone(self):
        self.assertTrue(is_valid_timezone("Asia/Kolkata"))
        self.assertFalse(is_valid_timezone("Not/A/Zone"))

    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_in_employee_defaults_to_kolkata(self, _mock_geo):
        tenant = Tenant.objects.create(name="Acme IN", domain="acme-in.test")
        branch = Branch.objects.create(
            tenant=tenant,
            name="HQ",
            code="HQ",
            address="1 Main",
            city="Mumbai",
            state="MH",
            country="India",
        )
        user = User.objects.create_user(
            username="in-user",
            email="in-user@test.com",
            password="pass",
            tenant=tenant,
        )
        Employee.objects.create(
            tenant=tenant,
            user=user,
            employee_code="E001",
            first_name="In",
            last_name="User",
            date_of_joining="2020-01-01",
            branch=branch,
            payroll_jurisdiction=JURISDICTION_IN,
        )
        request = _make_request()
        request.user = user
        tz = resolve_viewing_timezone(request, user=user)
        self.assertEqual(str(tz), "Asia/Kolkata")

    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_branch_timezone_overrides_jurisdiction(self, _mock_geo):
        tenant = Tenant.objects.create(name="Acme Branch", domain="acme-br.test")
        branch = Branch.objects.create(
            tenant=tenant,
            name="West",
            code="W1",
            address="1 Main",
            city="LA",
            state="CA",
            country="USA",
            timezone="America/Los_Angeles",
        )
        user = User.objects.create_user(
            username="us-branch-user",
            email="us-branch@test.com",
            password="pass",
            tenant=tenant,
        )
        Employee.objects.create(
            tenant=tenant,
            user=user,
            employee_code="E002",
            first_name="US",
            last_name="User",
            date_of_joining="2020-01-01",
            branch=branch,
            payroll_jurisdiction=JURISDICTION_US,
        )
        request = _make_request()
        request.user = user
        tz = resolve_viewing_timezone(request, user=user)
        self.assertEqual(str(tz), "America/Los_Angeles")

    @patch(
        "core.utils.fetch_ip_geo",
        return_value={"city": "Chicago", "country": "United States", "timezone": "America/Chicago"},
    )
    def test_us_employee_uses_ip_timezone(self, _mock_geo):
        tenant = Tenant.objects.create(name="Acme US", domain="acme-us.test")
        branch = Branch.objects.create(
            tenant=tenant,
            name="HQ",
            code="HQ",
            address="1 Main",
            city="Chicago",
            state="IL",
            country="USA",
            timezone="UTC",
        )
        user = User.objects.create_user(
            username="us-user",
            email="us-user@test.com",
            password="pass",
            tenant=tenant,
        )
        Employee.objects.create(
            tenant=tenant,
            user=user,
            employee_code="E003",
            first_name="US",
            last_name="User",
            date_of_joining="2020-01-01",
            branch=branch,
            payroll_jurisdiction=JURISDICTION_US,
        )
        request = _make_request(ip="198.51.100.20")
        request.user = user
        tz = resolve_viewing_timezone(request, user=user)
        self.assertEqual(str(tz), "America/Chicago")

    @patch("core.timezone_utils.get_employee_for_user")
    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_missing_branch_falls_back_to_jurisdiction(self, _mock_geo, mock_get_employee):
        user = SimpleNamespace(is_authenticated=True, tenant=None)
        mock_get_employee.return_value = SimpleNamespace(
            branch_id="dead-beef",
            branch=None,
            payroll_jurisdiction=JURISDICTION_IN,
        )
        request = _make_request()
        request.user = user
        tz = resolve_viewing_timezone(request, user=user)
        self.assertEqual(str(tz), "Asia/Kolkata")

    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_activate_viewing_timezone_without_request(self, _mock_geo):
        user = SimpleNamespace(
            is_authenticated=True,
            tenant=SimpleNamespace(enabled_jurisdictions=[JURISDICTION_IN]),
        )
        with patch("core.timezone_utils.get_employee_for_user", return_value=None):
            tz = activate_viewing_timezone(None, user=user)
        self.assertEqual(str(tz), "Asia/Kolkata")


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class TimezoneApiTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tz Tenant", domain="tz-tenant.test")
        self.branch = Branch.objects.create(
            tenant=self.tenant,
            name="India HQ",
            code="IHQ",
            address="1 Road",
            city="Mumbai",
            state="MH",
            country="India",
        )
        self.user = User.objects.create_user(
            username="tz-user",
            email="tz-user@test.com",
            password="pass",
            tenant=self.tenant,
        )
        Employee.objects.create(
            tenant=self.tenant,
            user=self.user,
            employee_code="TZ001",
            first_name="Tz",
            last_name="User",
            date_of_joining="2020-01-01",
            branch=self.branch,
            payroll_jurisdiction=JURISDICTION_IN,
        )
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_auth_me_includes_viewing_timezone(self, _mock_geo):
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["viewing_timezone"], "Asia/Kolkata")

    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_notification_created_at_serialized_in_regional_tz(self, _mock_geo):
        fixed_utc = datetime(2025, 6, 15, 10, 30, 0, tzinfo=dt_timezone.utc)
        with patch("django.utils.timezone.now", return_value=fixed_utc):
            Notification.objects.create(
                tenant=self.tenant,
                user=self.user,
                title="Test",
                message="Hello",
            )
        response = self.client.get("/api/v1/notifications/notifications/")
        self.assertEqual(response.status_code, 200)
        created_at = response.data["results"][0]["created_at"]
        self.assertIn("+05:30", created_at)

    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_audit_logs_remain_utc(self, _mock_geo):
        admin = User.objects.create_superuser(
            username="super",
            email="super@test.com",
            password="pass",
        )
        fixed_utc = datetime(2025, 6, 15, 10, 30, 0, tzinfo=dt_timezone.utc)
        with patch("django.utils.timezone.now", return_value=fixed_utc):
            SystemAuditLog.objects.create(
                tenant=self.tenant,
                user=admin,
                action="test.action",
                module="iam",
            )
        token = RefreshToken.for_user(admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        with patch("core.audit_clickhouse.fetch_logs_from_clickhouse", return_value=None):
            response = self.client.get("/api/v1/audit/platform-logs/")
        self.assertEqual(response.status_code, 200)
        created_at = response.data["results"][0]["created_at"]
        self.assertTrue(created_at.endswith("Z") or "+00:00" in created_at)

    @patch("core.utils.fetch_ip_geo", return_value=None)
    def test_activate_viewing_timezone_sets_localdate(self, _mock_geo):
        request = _make_request()
        request.user = self.user
        fixed_utc = datetime(2025, 6, 15, 20, 0, 0, tzinfo=dt_timezone.utc)
        with patch("django.utils.timezone.now", return_value=fixed_utc):
            activate_viewing_timezone(request, user=self.user)
            local_date = timezone.localdate()
        timezone.deactivate()
        self.assertEqual(local_date.isoformat(), "2025-06-16")
