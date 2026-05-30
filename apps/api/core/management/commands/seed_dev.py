import random
import uuid

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from core.models import Role, Tenant, TenantAddon, TenantEmailSettings, User, UserRoleMapping
from employees.models import Employee, EmployeeBank, EmployeeContact
from organization.models import Branch, Department, Designation

fake = Faker()

GENUINE_COMPANIES = [
    "TechNova Solutions", "Quantum Nexus Systems", "Apex Core Technologies",
    "BlueShift Analytics", "Vertex Global Services", "Pinnacle Dynamics",
    "Elevate Digital", "Lumina InfoTech", "Nexus Cloud Corp", "Prime Logic",
    "Zenith Engineering", "Stellar Innovations", "Aura Networks", "Crest IT Solutions",
    "Vanguard Tech Partners", "Horizon Data Services", "Summit Software", "Catalyst Solutions",
    "Pioneer Analytics", "Beacon Information Systems", "Oasis Software Systems"
]

GENUINE_FIRST_NAMES = [
    "Aarav", "Rohan", "Vikram", "Neha", "Priya", "Rahul", "Aditi", "Karan", "Siddharth",
    "Anita", "Sunil", "Kavita", "Sanjay", "Anjali", "Arjun", "Pooja", "Rajesh", "Nisha",
    "Alex", "David", "Emma", "Sarah", "Michael", "John", "Jessica", "Daniel", "Emily"
]

GENUINE_LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Singh", "Gupta", "Kumar", "Reddy", "Nair", "Iyer",
    "Jain", "Desai", "Rao", "Menon", "Joshi", "Kapoor", "Chopra", "Malhotra", "Mehta",
    "Smith", "Johnson", "Brown", "Taylor", "Anderson", "Thomas", "Jackson", "White"
]

PRIMARY_TENANT = {
    'name': 'Aastraa Demo',
    'domain': 'aastraa-demo',
    'email_domain': 'aastraa.com',
}

SAMPLE_TENANTS = [
    {'name': 'Astra Corp', 'domain': 'astra-corp', 'email_domain': 'astra.com'},
    {'name': 'Astra Net Ltd', 'domain': 'astra-net', 'email_domain': 'astra.net'},
]

TENANT_ROLES = [
    'Company Admin', 'HR Admin', 'Payroll Admin', 'Finance Admin',
    'IT Admin', 'Manager', 'Recruiter', 'Interviewer', 'Auditor', 'Employee',
]


def role_email_local(role_name: str) -> str:
    return role_name.lower().replace(' ', '')


def email_for_role(role_name: str, email_domain: str) -> str:
    if role_name == 'Super Admin':
        return f'superadmin@{email_domain}'
    return f'{role_email_local(role_name)}@{email_domain}'


class Command(BaseCommand):
    help = (
        'Seeds demo tenants, role users, and bulk sample companies for testing. '
        'Re-run to backfill branches and org structure on existing tenants.'
    )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database seed...')
        default_password = make_password('password123')

        from organization.services.tenant_provisioning import provision_tenant_defaults

        primary = self._ensure_tenant(**PRIMARY_TENANT)
        self._ensure_super_admin(primary.email_domain, default_password)
        provision_tenant_defaults(primary)
        self._seed_tenant_email_settings(primary)
        self._ensure_tenant_role_users(primary, TENANT_ROLES, default_password)
        self._link_role_users_to_employees(primary)
        self._seed_job_portal(primary)
        self._seed_demo_interview(primary)

        for sample in SAMPLE_TENANTS:
            tenant = self._ensure_tenant(**sample)
            provision_tenant_defaults(tenant)
            self._seed_tenant_email_settings(tenant)
            self._ensure_tenant_role_users(
                tenant,
                ['Employee', 'HR Admin', 'Manager'],
                default_password,
            )
            self._link_role_users_to_employees(tenant)

        self.stdout.write('Creating 100 bulk companies...')
        tenants = []
        for i in range(100):
            base_name = random.choice(GENUINE_COMPANIES)
            company_name = f'{base_name} {i+1}'
            slug = company_name.lower().replace(' ', '-') + str(random.randint(100, 9999))
            email_domain = f'{slug}.com'
            tenant, created = Tenant.objects.get_or_create(
                name=company_name,
                defaults={'domain': slug, 'email_domain': email_domain},
            )
            tenants.append(tenant)
            if not created:
                continue
            provision_tenant_defaults(tenant)
            self._seed_tenant_email_settings(tenant)

        self.stdout.write('Creating 500 employees across bulk tenants...')
        for tenant in tenants:
            branches = list(Branch.objects.filter(tenant=tenant))
            departments = list(Department.objects.filter(tenant=tenant))
            designations = list(Designation.objects.filter(tenant=tenant))
            domain = tenant.email_domain or 'example.com'

            for j in range(5):
                first_name = random.choice(GENUINE_FIRST_NAMES)
                last_name = random.choice(GENUINE_LAST_NAMES)
                email = f'{first_name.lower()}.{last_name.lower()}{j+1}@{domain}'

                user = User(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=default_password,
                    tenant=tenant,
                )
                user.save()

                emp = Employee.objects.create(
                    tenant=tenant,
                    user=user,
                    employee_code=f'EMP-{uuid.uuid4().hex[:8].upper()}',
                    first_name=first_name,
                    last_name=last_name,
                    gender=random.choice(['Male', 'Female']),
                    date_of_joining=fake.date_between(start_date='-5y', end_date='today'),
                    branch=random.choice(branches) if branches else None,
                    department=random.choice(departments) if departments else None,
                    designation=random.choice(designations) if designations else None,
                    status='Active',
                )

                EmployeeContact.objects.create(
                    tenant=tenant,
                    employee=emp,
                    personal_email=fake.email(),
                    mobile_number=fake.phone_number()[:20],
                    present_address=fake.address(),
                    permanent_address=fake.address(),
                    emergency_contact_name=fake.name(),
                    emergency_contact_number=fake.phone_number()[:20],
                )

                EmployeeBank.objects.create(
                    tenant=tenant,
                    employee=emp,
                    bank_name=fake.company() + ' Bank',
                    account_number=fake.bban(),
                    ifsc_code=fake.swift8(),
                    account_type='Savings',
                )

            self._assign_org_hierarchy(tenant)

        self._assign_org_hierarchy(primary)

        from django.core.management import call_command

        call_command("seed_env_config")

        self.stdout.write(
            self.style.SUCCESS(
                'Seed complete: primary demo tenant, sample tenants, 100 companies, 500 employees.'
            )
        )

    def _seed_tenant_email_settings(self, tenant):
        from django.conf import settings

        from_email = getattr(
            settings,
            'PLATFORM_DEFAULT_TENANT_FROM_EMAIL',
            'notifications@theastravision.com',
        )
        TenantEmailSettings.objects.update_or_create(
            tenant=tenant,
            defaults={
                'from_email': from_email,
                'from_name': tenant.name,
                'reply_to': from_email,
                'notify_roles': ['Company Admin', 'HR Admin'],
            },
        )

    def _seed_job_portal(self, tenant):
        from django.utils import timezone

        from recruitment.job_board_auth import generate_api_key
        from recruitment.models import JobRequisition, TenantCareerPortalSettings

        addon, _ = TenantAddon.objects.get_or_create(
            tenant=tenant,
            addon_code=TenantAddon.ADDON_JOB_PORTAL,
            defaults={'enabled': True, 'notes': 'Demo Job Portal add-on'},
        )
        if not addon.enabled:
            addon.enabled = True
            addon.save(update_fields=['enabled', 'updated_at'])

        if not TenantCareerPortalSettings.objects.filter(tenant=tenant).exists():
            full_key, prefix, key_hash = generate_api_key()
            TenantCareerPortalSettings.objects.create(
                tenant=tenant,
                slug=tenant.domain or 'aastraa-demo',
                api_key_hash=key_hash,
                api_key_prefix=prefix,
                company_blurb='Join Aastraa Demo — build the future of HR tech.',
                allowed_embed_origins=['http://localhost:3001', 'http://127.0.0.1:3001'],
            )
            self.stdout.write(
                self.style.WARNING(
                    f'Job Portal API key (save for testing): {full_key}'
                )
            )

        dept = Department.objects.filter(tenant=tenant).first()
        if not JobRequisition.objects.filter(tenant=tenant, slug='senior-software-engineer').exists():
            JobRequisition.objects.create(
                tenant=tenant,
                title='Senior Software Engineer',
                department=dept,
                location='Bengaluru, India',
                description=(
                    'We are looking for a Senior Software Engineer to build our HRMS platform. '
                    'You will work with Django, React, and AI services.'
                ),
                status='Open',
                slug='senior-software-engineer',
                is_published=True,
                published_at=timezone.now(),
                employment_type='Full-time',
                work_mode='Hybrid',
            )

    def _seed_demo_interview(self, tenant):
        """Ashish Mishra — Software Engineer AI interview link valid for 24h (demo)."""
        from datetime import timedelta

        from django.utils import timezone

        from recruitment.models import AiInterviewSession, Candidate, JobRequisition
        from recruitment.services import create_ai_session, get_magic_link

        demo_expiry_minutes = 24 * 60
        dept = Department.objects.filter(tenant=tenant).first()

        job, _ = JobRequisition.objects.get_or_create(
            tenant=tenant,
            slug='software-engineer',
            defaults={
                'title': 'Software Engineer',
                'department': dept,
                'location': 'Bengaluru, India',
                'description': (
                    'Software Engineer role for demo AI interviews. '
                    'Experience with Python, Django, React, and REST APIs.'
                ),
                'status': 'Open',
                'is_published': True,
                'published_at': timezone.now(),
                'employment_type': 'Full-time',
                'work_mode': 'Hybrid',
                'interview_question_count': 5,
            },
        )

        candidate, created = Candidate.objects.get_or_create(
            tenant=tenant,
            email='ashish.mishra@aastraa.com',
            job=job,
            defaults={
                'first_name': 'Ashish',
                'last_name': 'Mishra',
                'phone': '+91-9876543210',
                'stage': 'Interview',
                'parsed_resume_text': (
                    'Ashish Mishra — Software Engineer with 5+ years building web platforms '
                    'using Django, React, and PostgreSQL.'
                ),
                'ai_match_score': 88,
            },
        )
        if not created:
            candidate.first_name = 'Ashish'
            candidate.last_name = 'Mishra'
            candidate.stage = 'Interview'
            candidate.save(update_fields=['first_name', 'last_name', 'stage', 'updated_at'])

        expires_at = timezone.now() + timedelta(minutes=demo_expiry_minutes)
        session = (
            candidate.ai_sessions.order_by('-created_at').first()
        )
        if session:
            if session.status == 'expired':
                session.status = 'pending'
            session.expires_at = expires_at
            session.save(update_fields=['status', 'expires_at', 'updated_at'])
        else:
            session = create_ai_session(
                candidate,
                expiry_minutes=demo_expiry_minutes,
                include_assessment=False,
            )

        link = get_magic_link(session)
        self.stdout.write(
            self.style.SUCCESS(
                f'Demo AI interview: Ashish Mishra — {job.title} | status={session.status} | '
                f'expires_at={session.expires_at.isoformat()}'
            )
        )
        self.stdout.write(self.style.WARNING(f'Interview join link: {link}'))

        refreshed = AiInterviewSession.objects.filter(
            tenant=tenant,
            candidate__first_name='Ashish',
            candidate__last_name='Mishra',
            status='expired',
        ).update(status='pending', expires_at=expires_at)
        if refreshed:
            self.stdout.write(
                self.style.SUCCESS(f'Refreshed {refreshed} expired Ashish Mishra session(s).')
            )

    def _ensure_tenant(self, name, domain, email_domain):
        tenant, created = Tenant.objects.get_or_create(
            domain=domain,
            defaults={'name': name, 'email_domain': email_domain},
        )
        updated = False
        if tenant.name != name:
            tenant.name = name
            updated = True
        if tenant.email_domain != email_domain:
            tenant.email_domain = email_domain
            updated = True
        if updated:
            tenant.save()
        if created:
            self.stdout.write(f'Created tenant: {name} ({email_domain})')
        return tenant

    def _ensure_super_admin(self, email_domain, password):
        email = email_for_role('Super Admin', email_domain)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_superuser': True,
                'is_staff': True,
            },
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(f'Created Super Admin: {email} / password123')
        elif not user.check_password('password123'):
            user.set_password('password123')
            user.save(update_fields=['password'])

        role, _ = Role.objects.get_or_create(
            tenant=None,
            name='Super Admin',
            defaults={'description': 'Platform super administrator'},
        )
        UserRoleMapping.objects.get_or_create(user=user, role=role)

    def _ensure_tenant_role_users(self, tenant, role_names, password):
        for role_name in role_names:
            email = email_for_role(role_name, tenant.email_domain)
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': role_name.split()[0],
                    'last_name': role_name.split()[-1] if len(role_name.split()) > 1 else 'User',
                    'tenant': tenant,
                    'password': password,
                },
            )
            if not created:
                user.tenant = tenant
                user.save(update_fields=['tenant'])
            else:
                self.stdout.write(f'Created {role_name}: {email} / password123')

            role, _ = Role.objects.get_or_create(
                tenant=tenant,
                name=role_name,
                defaults={'description': role_name},
            )
            UserRoleMapping.objects.get_or_create(user=user, role=role)

    def _link_role_users_to_employees(self, tenant):
        """Link seeded role users to Employee records so ESS/WFH/attendance APIs work."""
        from datetime import date

        from employees.services.employee_types import assign_default_employee_type, seed_employee_types_for_tenant

        seed_employee_types_for_tenant(tenant.id)
        branch = Branch.objects.filter(tenant=tenant).first()
        department = Department.objects.filter(tenant=tenant).first()
        designation = Designation.objects.filter(tenant=tenant).first()

        link_roles = [
            'Company Admin', 'HR Admin', 'Payroll Admin', 'Finance Admin',
            'IT Admin', 'Manager', 'Recruiter', 'Interviewer', 'Auditor', 'Employee',
        ]
        for role_name in link_roles:
            email = email_for_role(role_name, tenant.email_domain)
            user = User.objects.filter(email=email, tenant=tenant).first()
            employee_code = f'EMP-{role_email_local(role_name).upper()[:12]}'
            if not user:
                continue
            if Employee.objects.filter(user=user).exists():
                continue
            if Employee.objects.filter(employee_code=employee_code).exists():
                Employee.objects.filter(employee_code=employee_code).update(user=user)
                continue
            emp = Employee.objects.create(
                tenant=tenant,
                user=user,
                employee_code=employee_code,
                first_name=user.first_name or role_name.split()[0],
                last_name=user.last_name or 'User',
                date_of_joining=date.today(),
                branch=branch,
                department=department,
                designation=designation,
                status='Active',
            )
            assign_default_employee_type(emp)

    def _assign_org_hierarchy(self, tenant):
        """Assign a simple reporting tree: manager@ as root, others report to root."""
        employees = list(
            Employee.objects.filter(tenant=tenant, status='Active').order_by(
                'date_of_joining', 'employee_code'
            )
        )
        if not employees:
            return

        domain = tenant.email_domain or 'aastraa.com'
        manager_user = User.objects.filter(email=f'manager@{domain}').first()
        root = None
        if manager_user:
            root = Employee.objects.filter(tenant=tenant, user=manager_user).first()

        if not root:
            root = employees[0]
        root.reporting_manager = None
        root.save(update_fields=['reporting_manager'])

        for emp in employees:
            if emp.pk == root.pk:
                continue
            if emp.reporting_manager_id != root.pk:
                emp.reporting_manager = root
                emp.save(update_fields=['reporting_manager'])
