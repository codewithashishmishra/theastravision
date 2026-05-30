"""Default org structure when a tenant is created or seeded."""

from __future__ import annotations

from typing import TypedDict

from core.models import Tenant
from organization.models import Branch, CompanyProfile, Department, Designation

DEFAULT_DEPARTMENTS = [
    ('HR', 'HR'),
    ('ENG', 'Engineering'),
    ('SAL', 'Sales'),
    ('MKT', 'Marketing'),
]

DEFAULT_DESIGNATIONS = [
    ('MGR', 'Manager'),
    ('DEV', 'Developer'),
    ('EXE', 'Executive'),
    ('ANL', 'Analyst'),
]


class BranchSpec(TypedDict):
    code: str
    name: str
    address: str
    city: str
    state: str
    country: str
    is_head_office: bool


BRANCH_TEMPLATES: dict[str, list[BranchSpec]] = {
    'aastraa-demo': [
        {
            'code': 'BR-HQ',
            'name': 'Bengaluru HQ',
            'address': '100 MG Road',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'country': 'India',
            'is_head_office': True,
        },
        {
            'code': 'BR-MUM',
            'name': 'Mumbai Office',
            'address': '50 Bandra Kurla Complex',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'country': 'India',
            'is_head_office': False,
        },
        {
            'code': 'BR-DEL',
            'name': 'Delhi Office',
            'address': '12 Connaught Place',
            'city': 'New Delhi',
            'state': 'Delhi',
            'country': 'India',
            'is_head_office': False,
        },
    ],
    'astra-corp': [
        {
            'code': 'BR-HQ',
            'name': 'Astra Corp HQ',
            'address': '1 Tech Park Road',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'country': 'India',
            'is_head_office': True,
        },
        {
            'code': 'BR-REG',
            'name': 'Regional Office',
            'address': '22 Industrial Area',
            'city': 'Pune',
            'state': 'Maharashtra',
            'country': 'India',
            'is_head_office': False,
        },
    ],
    'astra-net': [
        {
            'code': 'BR-HQ',
            'name': 'Astra Net HQ',
            'address': '5 Cyber City',
            'city': 'Gurugram',
            'state': 'Haryana',
            'country': 'India',
            'is_head_office': True,
        },
        {
            'code': 'BR-REG',
            'name': 'Regional Office',
            'address': '8 IT Corridor',
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'country': 'India',
            'is_head_office': False,
        },
    ],
}

DEFAULT_BRANCHES: list[BranchSpec] = [
    {
        'code': 'BR-HQ',
        'name': 'Head Office',
        'address': '1 Main Street',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'country': 'India',
        'is_head_office': True,
    },
    {
        'code': 'BR-02',
        'name': 'Branch 2',
        'address': '2 Secondary Road',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'country': 'India',
        'is_head_office': False,
    },
]


def branch_specs_for_tenant(tenant: Tenant) -> list[BranchSpec]:
    domain = (tenant.domain or '').strip().lower()
    if domain in BRANCH_TEMPLATES:
        return BRANCH_TEMPLATES[domain]
    return DEFAULT_BRANCHES


def provision_tenant_defaults(tenant: Tenant) -> None:
    """Idempotent: company profile, branches, departments, designations, employee types."""
    from employees.services.employee_types import seed_employee_types_for_tenant

    CompanyProfile.objects.get_or_create(
        tenant=tenant,
        defaults={
            'legal_name': tenant.name,
            'registration_number': f'REG-{tenant.domain or tenant.id}',
            'tax_id': '',
            'website': f'https://{tenant.domain or "company"}.example.com',
            'logo': f'https://ui-avatars.com/api/?name={tenant.name.replace(" ", "+")}',
        },
    )

    for spec in branch_specs_for_tenant(tenant):
        Branch.objects.get_or_create(
            tenant=tenant,
            code=spec['code'],
            defaults={
                'name': spec['name'],
                'address': spec['address'],
                'city': spec['city'],
                'state': spec['state'],
                'country': spec['country'],
                'is_head_office': spec['is_head_office'],
                'timezone': 'Asia/Kolkata',
            },
        )

    for code, name in DEFAULT_DEPARTMENTS:
        Department.objects.get_or_create(
            tenant=tenant,
            code=code,
            defaults={'name': name},
        )

    for code, name in DEFAULT_DESIGNATIONS:
        Designation.objects.get_or_create(
            tenant=tenant,
            code=code,
            defaults={'name': name},
        )

    seed_employee_types_for_tenant(tenant.id)
