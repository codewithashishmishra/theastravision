from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Permission, Role, Tenant, User, UserRoleMapping
from employees.models import Employee
from organization.models import Department
from wfh.models import WFHPolicy, WFHRequest


WFH_PERMISSIONS = [
    ("wfh.request.create", "Create WFH request"),
    ("wfh.approve.manager", "Approve WFH as manager"),
    ("wfh.approve.hr", "Approve WFH as HR"),
    ("wfh.view.all", "View all WFH tracking data"),
    ("wfh.policy.manage", "Manage WFH policy"),
    ("wfh.admin.settings", "Manage tracker admin settings"),
]


class Command(BaseCommand):
    help = "Seed WFH permissions and default policy per tenant"

    def handle(self, *args, **options):
        perms = []
        for code, name in WFH_PERMISSIONS:
            p, _ = Permission.objects.get_or_create(code=code, defaults={"name": name})
            perms.append(p)
        self.stdout.write(f"Ensured {len(perms)} WFH permissions")

        for tenant in Tenant.objects.all()[:20]:
            WFHPolicy.objects.get_or_create(
                tenant=tenant,
                is_active=True,
                defaults={
                    "require_hr_approval": True,
                    "screenshot_interval_seconds": 15,
                    "idle_threshold_seconds": 300,
                    "screenshot_retention_days": 30,
                },
            )
            role, _ = Role.objects.get_or_create(tenant=tenant, name="HR Admin", defaults={"description": "HR"})
            role.permissions.add(*perms)

        self._assign_admin_tenants_and_roles(perms)
        self._ensure_demo_employees()
        self._seed_today_wfh_for_demo_employee()
        self._seed_sample_approval_queue()
        self.stdout.write(self.style.SUCCESS("WFH seed complete"))

    def _primary_tenant(self):
        return (
            Tenant.objects.filter(email_domain='aastraa.com').first()
            or Tenant.objects.filter(domain='aastraa-demo').first()
            or Tenant.objects.first()
        )

    def _assign_admin_tenants_and_roles(self, perms):
        tenant = self._primary_tenant()
        if not tenant:
            return
        domain = tenant.email_domain or 'aastraa.com'
        for local in ('hradmin', 'companyadmin'):
            email = f'{local}@{domain}'
            user = User.objects.filter(email=email).first()
            if not user:
                continue
            if not user.tenant_id:
                user.tenant = tenant
                user.save(update_fields=["tenant"])
                self.stdout.write(f"Assigned tenant to {email}")
        hr_user = User.objects.filter(email=f'hradmin@{domain}').first()
        if hr_user and hr_user.tenant_id:
            role, _ = Role.objects.get_or_create(
                tenant=hr_user.tenant, name="HR Admin", defaults={"description": "HR"}
            )
            role.permissions.add(*perms)
            UserRoleMapping.objects.get_or_create(user=hr_user, role=role)
            self.stdout.write(f"Linked hradmin@{domain} to HR Admin role with WFH permissions")

    def _ensure_demo_employees(self):
        """Link role test users to Employee profiles (required for tracker login)."""
        tenant = self._primary_tenant()
        if not tenant:
            return
        domain = tenant.email_domain or 'aastraa.com'
        dept, _ = Department.objects.get_or_create(
            tenant=tenant, code="GEN", defaults={"name": "General"}
        )
        demos = [
            (f"employee@{domain}", "EMP-DEMO-001", "Demo", "Employee"),
            (f"manager@{domain}", "MGR-DEMO-001", "Demo", "Manager"),
        ]
        manager_emp = None
        for email, code, first, last in demos:
            user = User.objects.filter(email=email).first()
            if not user:
                continue
            if not user.tenant_id:
                user.tenant = tenant
                user.save(update_fields=["tenant"])
            emp, created = Employee.objects.get_or_create(
                employee_code=code,
                defaults={
                    "tenant": tenant,
                    "user": user,
                    "first_name": first,
                    "last_name": last,
                    "date_of_joining": date.today(),
                    "department": dept,
                    "status": "Active",
                },
            )
            if not created and emp.user_id != user.id:
                emp.user = user
                emp.save(update_fields=["user"])
            if "manager" in email:
                manager_emp = emp
        if manager_emp:
            Employee.objects.filter(employee_code="EMP-DEMO-001").update(reporting_manager=manager_emp)
        self.stdout.write("Ensured Employee profiles for employee@ / manager@ test users")

    def _seed_today_wfh_for_demo_employee(self):
        """Approved WFH for today so tracker Start Work is enabled."""
        today = timezone.localdate()
        tenant = self._primary_tenant()
        domain = (tenant.email_domain if tenant else None) or 'aastraa.com'
        employee_email = f'employee@{domain}'
        user = User.objects.filter(email=employee_email).first()
        if not user:
            self.stdout.write(self.style.WARNING(f"{employee_email} not found — skip WFH seed"))
            return
        employee = Employee.objects.filter(user=user).first()
        if not employee:
            self.stdout.write(self.style.WARNING(f"No Employee for {employee_email} — run seed first"))
            return

        req, created = WFHRequest.objects.update_or_create(
            tenant=employee.tenant,
            employee=employee,
            start_date=today,
            end_date=today,
            defaults={
                "request_date": today,
                "reason": "Demo WFH — tracker testing",
                "status": WFHRequest.STATUS_HR_APPROVED,
                "approval_date": timezone.now(),
                "remarks": "Auto-seeded for development",
            },
        )
        if req.status != WFHRequest.STATUS_HR_APPROVED:
            req.status = WFHRequest.STATUS_HR_APPROVED
            req.approval_date = timezone.now()
            req.save(update_fields=["status", "approval_date", "updated_at"])
        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} approved WFH for {employee_email} on {today}"
            )
        )

    def _seed_sample_approval_queue(self):
        """Pending + manager-approved requests for HR/manager UI testing."""
        employee = Employee.objects.filter(employee_code="EMP-DEMO-001").first()
        if not employee:
            return
        today = timezone.localdate()
        pending_start = today + timedelta(days=7)
        mgr_start = today + timedelta(days=14)

        WFHRequest.objects.update_or_create(
            tenant=employee.tenant,
            employee=employee,
            start_date=pending_start,
            end_date=pending_start,
            defaults={
                "request_date": today,
                "reason": "Demo pending WFH — awaiting manager/HR",
                "status": WFHRequest.STATUS_PENDING,
            },
        )
        WFHRequest.objects.update_or_create(
            tenant=employee.tenant,
            employee=employee,
            start_date=mgr_start,
            end_date=mgr_start,
            defaults={
                "request_date": today,
                "reason": "Demo WFH — manager approved, awaiting HR",
                "status": WFHRequest.STATUS_MANAGER_APPROVED,
            },
        )
        self.stdout.write("Seeded pending and manager-approved sample WFH requests")
