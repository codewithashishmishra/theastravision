from django.core.management.base import BaseCommand

from core.models import Tenant
from employees.models import Employee, EmployeeTax, EmployeeTaxProfile
from organization.models import CompanyProfile, LegalEntity


class Command(BaseCommand):
    help = 'Backfill jurisdiction data for existing tenants and employees'

    def handle(self, *args, **options):
        for tenant in Tenant.objects.all():
            if not tenant.enabled_jurisdictions:
                tenant.enabled_jurisdictions = ['IN']
                tenant.save(update_fields=['enabled_jurisdictions', 'default_currency', 'fiscal_year_start_month'])

            if not LegalEntity.objects.filter(tenant=tenant, jurisdiction='IN').exists():
                profile = CompanyProfile.objects.filter(tenant=tenant).first()
                LegalEntity.objects.create(
                    tenant=tenant,
                    jurisdiction='IN',
                    legal_name=profile.legal_name if profile else tenant.name,
                    registration_number=profile.registration_number if profile else None,
                    tax_id=profile.tax_id if profile else None,
                    is_default_for_jurisdiction=True,
                )

            default_entity = LegalEntity.objects.filter(
                tenant=tenant, jurisdiction='IN', is_default_for_jurisdiction=True
            ).first()

            Employee.objects.filter(tenant=tenant, payroll_jurisdiction__isnull=True).update(
                payroll_jurisdiction='IN'
            )
            if default_entity:
                Employee.objects.filter(tenant=tenant, legal_entity__isnull=True).update(
                    legal_entity=default_entity
                )

            for tax in EmployeeTax.objects.filter(tenant=tenant):
                EmployeeTaxProfile.objects.update_or_create(
                    tenant=tenant,
                    employee=tax.employee,
                    jurisdiction='IN',
                    defaults={
                        'fields': {
                            'pan_number': tax.pan_number,
                            'aadhaar_number': tax.aadhaar_number,
                            'uan_number': tax.uan_number or '',
                            'pf_number': tax.pf_number or '',
                            'esic_number': tax.esic_number or '',
                            'tax_regime': 'new',
                        },
                    },
                )

        self.stdout.write(self.style.SUCCESS('Jurisdiction backfill complete.'))
