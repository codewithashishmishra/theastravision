import random
import uuid

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from core.models import Role, Tenant, TenantAddon, User, UserRoleMapping
from employees.models import Employee, EmployeeBank, EmployeeContact
from organization.models import Branch, CompanyProfile, Department, Designation

fake = Faker()

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
    help = 'Seeds demo tenants, role users, and bulk sample companies for testing'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database seed...')
        default_password = make_password('password123')

        primary = self._ensure_tenant(**PRIMARY_TENANT)
        self._ensure_company_profile(primary)
        self._ensure_super_admin(primary.email_domain, default_password)
        self._ensure_tenant_role_users(primary, TENANT_ROLES, default_password)
        self._seed_job_portal(primary)

        for sample in SAMPLE_TENANTS:
            tenant = self._ensure_tenant(**sample)
            self._ensure_company_profile(tenant)
            self._ensure_tenant_role_users(
                tenant,
                ['Employee', 'HR Admin'],
                default_password,
            )

        self.stdout.write('Creating 100 bulk companies...')
        tenants = []
        for _ in range(100):
            slug = fake.domain_word() + str(random.randint(100, 99999))
            email_domain = f'{slug}.test'
            tenant = Tenant.objects.create(
                name=f'{fake.company()} - {fake.unique.random_int(min=1000, max=9999)}',
                domain=slug,
                email_domain=email_domain,
            )
            tenants.append(tenant)
            self._ensure_company_profile(tenant)
            self._seed_org_structure(tenant)

        self.stdout.write('Creating 500 employees across bulk tenants...')
        for tenant in tenants:
            branches = list(Branch.objects.filter(tenant=tenant))
            departments = list(Department.objects.filter(tenant=tenant))
            designations = list(Designation.objects.filter(tenant=tenant))
            domain = tenant.email_domain or 'example.com'

            for _ in range(5):
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f'{first_name.lower()}.{last_name.lower()}@{domain}'

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

        from django.core.management import call_command

        call_command("seed_env_config")

        self.stdout.write(
            self.style.SUCCESS(
                'Seed complete: primary demo tenant, sample tenants, 100 companies, 500 employees.'
            )
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

    def _ensure_company_profile(self, tenant):
        CompanyProfile.objects.get_or_create(
            tenant=tenant,
            defaults={
                'legal_name': tenant.name,
                'registration_number': f'REG-{fake.bothify(text="????-####").upper()}',
                'tax_id': f'TAX-{fake.bothify(text="######")}',
                'website': fake.url(),
                'logo': f'https://ui-avatars.com/api/?name={tenant.name.replace(" ", "+")}',
            },
        )

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

    def _seed_org_structure(self, tenant):
        for suffix in ('01', '02'):
            Branch.objects.get_or_create(
                tenant=tenant,
                code=f'BR-{suffix}',
                defaults={
                    'name': fake.city() + ' Branch',
                    'address': fake.address(),
                    'city': fake.city(),
                    'state': fake.state(),
                    'country': fake.country(),
                },
            )
        for dept_name in ['HR', 'Engineering', 'Sales', 'Marketing']:
            Department.objects.get_or_create(
                tenant=tenant,
                code=dept_name[:3].upper(),
                defaults={'name': dept_name},
            )
        for desig in ['Manager', 'Developer', 'Executive', 'Analyst']:
            Designation.objects.get_or_create(
                tenant=tenant,
                code=desig[:3].upper(),
                defaults={'name': desig},
            )
