"""Encrypt existing plaintext PAN, Aadhaar, and bank account values."""

from django.core.management.base import BaseCommand

from core.field_crypto import ENC_PREFIX, encrypt_stored_field
from employees.models import EmployeeBank, EmployeeTax


class Command(BaseCommand):
    help = 'Encrypt existing employee tax and bank PII stored in plaintext'

    def handle(self, *args, **options):
        tax_fields = ('pan_number', 'aadhaar_number', 'uan_number', 'pf_number', 'esic_number')
        tax_updated = 0
        for row in EmployeeTax.objects.all().iterator():
            changed = False
            for field in tax_fields:
                value = getattr(row, field, '') or ''
                if value and not str(value).startswith(ENC_PREFIX):
                    setattr(row, field, encrypt_stored_field(value, field))
                    changed = True
            if changed:
                row.save(update_fields=list(tax_fields))
                tax_updated += 1

        bank_updated = 0
        for row in EmployeeBank.objects.all().iterator():
            value = row.account_number or ''
            if value and not str(value).startswith(ENC_PREFIX):
                row.account_number = encrypt_stored_field(value, 'bank_account_number')
                row.save(update_fields=['account_number'])
                bank_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Encrypted PII for {tax_updated} tax record(s) and {bank_updated} bank record(s).'
            )
        )
