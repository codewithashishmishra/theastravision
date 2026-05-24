"""Celery tasks for bulk compliance document generation."""

from celery import shared_task

from core.models import Tenant
from employees.models import Employee
from payroll.models import Payslip

from .services import (
    generate_form16_pdf,
    generate_w2_pdf,
    generate_t4_pdf,
    generate_1095c_pdf,
    save_compliance_document,
)


@shared_task
def bulk_generate_year_end_documents(tenant_id: str, fiscal_year: int):
    tenant = Tenant.objects.get(id=tenant_id)
    jurisdictions = tenant.enabled_jurisdictions or ['IN']

    if 'IN' in jurisdictions:
        for emp in Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='IN', status='Active'):
            payslips = Payslip.objects.filter(
                tenant_id=tenant_id,
                employee=emp,
                jurisdiction='IN',
                payroll_run__year__gte=fiscal_year,
                payroll_run__year__lte=fiscal_year + 1,
            ).prefetch_related('line_items')
            if payslips.exists():
                pdf, meta = generate_form16_pdf(tenant, emp, emp.legal_entity, fiscal_year, payslips)
                save_compliance_document(tenant_id, emp, 'IN', 'FORM16', fiscal_year, pdf, meta)

    if 'US' in jurisdictions:
        for emp in Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='US', status='Active'):
            payslips = Payslip.objects.filter(
                tenant_id=tenant_id,
                employee=emp,
                jurisdiction='US',
                payroll_run__year=fiscal_year,
            ).prefetch_related('line_items')
            if payslips.exists():
                pdf, meta = generate_w2_pdf(tenant, emp, emp.legal_entity, fiscal_year, payslips)
                save_compliance_document(tenant_id, emp, 'US', 'W2', fiscal_year, pdf, meta)
            pdf1095, meta1095 = generate_1095c_pdf(tenant, emp, emp.legal_entity, fiscal_year)
            save_compliance_document(tenant_id, emp, 'US', 'FORM1095C', fiscal_year, pdf1095, meta1095)

    if 'CA' in jurisdictions:
        for emp in Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='CA', status='Active'):
            payslips = Payslip.objects.filter(
                tenant_id=tenant_id,
                employee=emp,
                jurisdiction='CA',
                payroll_run__year=fiscal_year,
            ).prefetch_related('line_items')
            if payslips.exists():
                pdf, meta = generate_t4_pdf(tenant, emp, emp.legal_entity, fiscal_year, payslips)
                save_compliance_document(tenant_id, emp, 'CA', 'T4', fiscal_year, pdf, meta)
