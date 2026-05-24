import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Tenant
from organization.models import CompanyProfile, Branch, Department, Designation

def seed():
    # 1. Ensure we have at least one Tenant
    tenant, created = Tenant.objects.get_or_create(
        name="Aastraa Default Tenant",
        defaults={
            "domain": "aastraa.local",
            "email_domain": "aastraa.com"
        }
    )
    if created:
        print(f"Created Tenant: {tenant.name}")
    else:
        print(f"Using existing Tenant: {tenant.name}")

    # 2. Seed Company Profile
    if not CompanyProfile.objects.filter(tenant=tenant).exists():
        CompanyProfile.objects.create(
            tenant=tenant,
            legal_name="Aastraa Global Technologies Inc.",
            registration_number="REG-123456789",
            tax_id="TAX-987654321",
            website="https://www.aastraa.com"
        )
        print("Seeded CompanyProfile.")
    else:
        print("CompanyProfile already exists.")

    # 3. Seed Branches
    if not Branch.objects.filter(tenant=tenant).exists():
        branches = [
            {"name": "Global Headquarters", "code": "HQ", "city": "New York", "state": "NY", "country": "USA", "is_head_office": True},
            {"name": "EMEA Hub", "code": "EMEA", "city": "London", "state": "England", "country": "UK", "is_head_office": False},
            {"name": "APAC Hub", "code": "APAC", "city": "Singapore", "state": "Singapore", "country": "Singapore", "is_head_office": False},
        ]
        for b in branches:
            Branch.objects.create(tenant=tenant, address="123 Corporate Way", **b)
        print("Seeded Branches.")
    else:
        print("Branches already exist.")

    # 4. Seed Departments
    if not Department.objects.filter(tenant=tenant).exists():
        departments = [
            {"name": "Engineering", "code": "ENG"},
            {"name": "Human Resources", "code": "HR"},
            {"name": "Sales & Marketing", "code": "SM"},
            {"name": "Finance", "code": "FIN"},
        ]
        for d in departments:
            Department.objects.create(tenant=tenant, **d)
        print("Seeded Departments.")
    else:
        print("Departments already exist.")

    # 5. Seed Designations
    if not Designation.objects.filter(tenant=tenant).exists():
        designations = [
            {"name": "Software Engineer", "code": "SE1"},
            {"name": "Senior Software Engineer", "code": "SE2"},
            {"name": "HR Manager", "code": "HRM"},
            {"name": "Account Executive", "code": "AE"},
            {"name": "Financial Analyst", "code": "FA"},
        ]
        for des in designations:
            Designation.objects.create(tenant=tenant, **des)
        print("Seeded Designations.")
    else:
        print("Designations already exist.")

if __name__ == "__main__":
    seed()
