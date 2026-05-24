"""Compliance document and export generation."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

from compliance.models import ComplianceDocument
from compliance.pdf_fill import fill_government_pdf, pdf_from_text
from payroll.models import Payslip


def _line_sum(payslip, code: str) -> Decimal:
    return sum(li.amount for li in payslip.line_items.all() if li.statutory_code == code)


def _employer_label(tenant, legal_entity) -> str:
    return legal_entity.legal_name if legal_entity else tenant.name


def _employee_tax_id(employee, jurisdiction: str) -> str:
    profile = employee.tax_profiles.filter(jurisdiction=jurisdiction).first()
    if profile and profile.fields:
        if jurisdiction == 'IN':
            return profile.fields.get('pan_number', '') or ''
        if jurisdiction == 'US':
            return profile.fields.get('ssn', '') or ''
        if jurisdiction == 'CA':
            return profile.fields.get('sin', '') or ''
    tax = getattr(employee, 'tax_details', None)
    if tax and jurisdiction == 'IN':
        return tax.pan_number or ''
    return ''


def generate_form16_pdf(tenant, employee, legal_entity, fy: int, payslips) -> tuple[bytes, dict]:
    total_gross = sum(p.gross_pay for p in payslips)
    total_tds = sum(_line_sum(p, 'TDS') for p in payslips)
    employer = _employer_label(tenant, legal_entity)
    emp_name = f'{employee.first_name} {employee.last_name}'
    lines = [
        f'Employer: {employer}',
        f'Employee: {emp_name} ({employee.employee_code})',
        f'PAN: {_employee_tax_id(employee, "IN")}',
        f'Financial Year: {fy}-{fy + 1}',
        f'Gross Salary: INR {total_gross}',
        f'TDS Deducted: INR {total_tds}',
        '',
        'Part A: TDS details as per payroll records.',
        'Part B: Salary breakdown from payslips.',
        '',
        'Disclaimer: Review with a qualified CA before filing.',
    ]
    data = {
        'employer_name': employer,
        'employee_name': emp_name,
        'pan': _employee_tax_id(employee, 'IN'),
        'gross_salary': str(total_gross),
        'tds_deducted': str(total_tds),
    }
    return fill_government_pdf('IN', 'FORM16', fy, data, lines, 'Form 16 Certificate')


def generate_form12ba_pdf(tenant, employee, legal_entity, fy: int, perks: dict) -> tuple[bytes, dict]:
    employer = _employer_label(tenant, legal_entity)
    emp_name = f'{employee.first_name} {employee.last_name}'
    lines = [
        f'Employer: {employer}',
        f'Employee: {emp_name}',
        f'Financial Year: {fy}-{fy + 1}',
        '',
        'Perquisites (Form 12BA):',
    ]
    for key, val in (perks or {}).items():
        lines.append(f'  {key}: INR {val}')
    if not perks:
        lines.append('  No perquisites recorded.')
    lines.append('')
    lines.append('Disclaimer: Review with a qualified CA before filing.')
    return fill_government_pdf('IN', 'FORM12BA', fy, {'employee_name': emp_name}, lines, 'Form 12BA')


def generate_w2_pdf(tenant, employee, legal_entity, tax_year: int, payslips) -> tuple[bytes, dict]:
    wages = sum(p.gross_pay for p in payslips)
    fed = sum(_line_sum(p, 'FED_WH') for p in payslips)
    ss = sum(_line_sum(p, 'FICA_SS') for p in payslips)
    med = sum(_line_sum(p, 'FICA_MED') for p in payslips)
    employer = _employer_label(tenant, legal_entity)
    ein = (legal_entity.tax_id if legal_entity else '') or ''
    emp_name = f'{employee.first_name} {employee.last_name}'
    lines = [
        f'Employer: {employer}',
        f'Employee: {emp_name}',
        f'Tax Year: {tax_year}',
        f'Box 1 Wages: USD {wages}',
        f'Box 2 Federal tax withheld: USD {fed}',
        f'Box 4 Social Security tax: USD {ss}',
        f'Box 6 Medicare tax: USD {med}',
        '',
        'Disclaimer: Review with a qualified tax professional before filing.',
    ]
    parts = emp_name.split(None, 1)
    data = {
        'employer_name': employer,
        'employer_ein': ein,
        'employee_name': emp_name,
        'employee_first_name': parts[0] if parts else '',
        'employee_last_name': parts[1] if len(parts) > 1 else '',
        'employee_ssn': _employee_tax_id(employee, 'US'),
        'box1_wages': f'{wages:.2f}',
        'box2_federal_tax': f'{fed:.2f}',
        'box4_ss_tax': f'{ss:.2f}',
        'box6_medicare_tax': f'{med:.2f}',
    }
    return fill_government_pdf('US', 'W2', tax_year, data, lines, 'Form W-2 Wage and Tax Statement')


def generate_1095c_pdf(tenant, employee, legal_entity, tax_year: int, offer_code: str = '1A') -> tuple[bytes, dict]:
    employer = _employer_label(tenant, legal_entity)
    ein = (legal_entity.tax_id if legal_entity else '') or ''
    emp_name = f'{employee.first_name} {employee.last_name}'
    lines = [
        f'Employer: {employer}',
        f'Employee: {emp_name}',
        f'Tax Year: {tax_year}',
        f'Offer of coverage code: {offer_code}',
        '',
        'ACA Form 1095-C employer-provided health insurance offer and coverage.',
        'Disclaimer: Confirm with benefits administrator before filing.',
    ]
    parts = emp_name.split(None, 1)
    data = {
        'employer_name': employer,
        'employer_ein': ein,
        'employee_name': emp_name,
        'employee_first_name': parts[0] if parts else '',
        'employee_last_name': parts[1] if len(parts) > 1 else '',
        'employee_ssn': _employee_tax_id(employee, 'US'),
        'offer_of_coverage': offer_code,
    }
    return fill_government_pdf('US', 'FORM1095C', tax_year, data, lines, 'Form 1095-C')


def generate_t4_pdf(tenant, employee, legal_entity, tax_year: int, payslips) -> tuple[bytes, dict]:
    income = sum(p.gross_pay for p in payslips)
    cpp = sum(_line_sum(p, 'CPP') for p in payslips)
    ei = sum(_line_sum(p, 'EI') for p in payslips)
    fed = sum(_line_sum(p, 'FED_TAX') for p in payslips)
    employer = _employer_label(tenant, legal_entity)
    emp_name = f'{employee.first_name} {employee.last_name}'
    lines = [
        f'Employer: {employer}',
        f'Employee: {emp_name}',
        f'Tax Year: {tax_year}',
        f'Box 14 Employment income: CAD {income}',
        f'Box 16 CPP contributions: CAD {cpp}',
        f'Box 18 EI premiums: CAD {ei}',
        f'Box 22 Income tax deducted: CAD {fed}',
        '',
        'Disclaimer: Review with a qualified tax professional before filing.',
    ]
    data = {
        'employer_name': employer,
        'employee_name': emp_name,
        'box14_income': f'{income:.2f}',
        'box16_cpp': f'{cpp:.2f}',
        'box18_ei': f'{ei:.2f}',
        'box22_tax': f'{fed:.2f}',
    }
    return fill_government_pdf('CA', 'T4', tax_year, data, lines, 'T4 Statement of Remuneration Paid')


def generate_rl1_pdf(tenant, employee, legal_entity, tax_year: int, payslips) -> tuple[bytes, dict]:
    income = sum(p.gross_pay for p in payslips)
    qpp = sum(_line_sum(p, 'CPP') for p in payslips)
    emp_name = f'{employee.first_name} {employee.last_name}'
    employer = _employer_label(tenant, legal_entity)
    lines = [
        f'Employer: {employer}',
        f'Employee: {emp_name}',
        f'Tax Year: {tax_year}',
        f'Quebec employment income: CAD {income}',
        f'QPP contributions: CAD {qpp}',
        '',
        'Relevé 1 — Quebec provincial slip.',
        'Disclaimer: Review with a qualified tax professional before filing.',
    ]
    return fill_government_pdf(
        'CA', 'RL1', tax_year, {'employee_name': emp_name, 'income': f'{income:.2f}'}, lines, 'RL-1 Relevé'
    )


def generate_ecr_csv(tenant_id, jurisdiction, month, year) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['UAN', 'Employee Name', 'Gross Wages', 'EPF Wages', 'EPF EE', 'EPF ER', 'EPS', 'EDLI'])
    payslips = Payslip.objects.filter(
        tenant_id=tenant_id,
        jurisdiction=jurisdiction,
        payroll_run__month=month,
        payroll_run__year=year,
    ).select_related('employee').prefetch_related('line_items', 'employee__tax_details')
    for ps in payslips:
        pf_ee = _line_sum(ps, 'PF_EE')
        pf_er = _line_sum(ps, 'PF_ER')
        uan = ''
        if hasattr(ps.employee, 'tax_details') and ps.employee.tax_details:
            uan = ps.employee.tax_details.uan_number or ps.employee.employee_code
        writer.writerow([
            uan or ps.employee.employee_code,
            f'{ps.employee.first_name} {ps.employee.last_name}',
            ps.gross_pay,
            ps.gross_pay * Decimal('0.4'),
            pf_ee,
            pf_er,
            pf_er * Decimal('0.67'),
            pf_er * Decimal('0.01'),
        ])
    return output.getvalue()


def generate_941_export(tenant_id, jurisdiction, quarter: int, year: int) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Quarter', 'Year', 'Employee', 'Wages', 'Federal WH', 'SS Tax', 'Medicare Tax'])
    month_start = (quarter - 1) * 3 + 1
    months = [month_start, month_start + 1, month_start + 2]
    payslips = Payslip.objects.filter(
        tenant_id=tenant_id,
        jurisdiction=jurisdiction,
        payroll_run__year=year,
        payroll_run__month__in=months,
    ).select_related('employee').prefetch_related('line_items')
    for ps in payslips:
        writer.writerow([
            quarter,
            year,
            f'{ps.employee.first_name} {ps.employee.last_name}',
            ps.gross_pay,
            _line_sum(ps, 'FED_WH'),
            _line_sum(ps, 'FICA_SS'),
            _line_sum(ps, 'FICA_MED'),
        ])
    return output.getvalue()


def generate_itr_assist(tenant, employee, fy: int, payslips) -> dict:
    gross = sum(p.gross_pay for p in payslips)
    tds = sum(_line_sum(p, 'TDS') for p in payslips)
    return {
        'form': 'ITR-1',
        'financial_year': f'{fy}-{fy + 1}',
        'employee': f'{employee.first_name} {employee.last_name}',
        'pan': _employee_tax_id(employee, 'IN'),
        'fields': {
            'salary_income': str(gross),
            'tds_claimed': str(tds),
            'taxable_income': str(gross),
            'note': 'Pre-fill assist only — not e-filed to incometax.gov.in',
        },
    }


def generate_us_1040_prep(tenant, employee, tax_year: int, payslips) -> dict:
    wages = sum(p.gross_pay for p in payslips)
    fed = sum(_line_sum(p, 'FED_WH') for p in payslips)
    return {
        'form': '1040-prep',
        'tax_year': tax_year,
        'employee': f'{employee.first_name} {employee.last_name}',
        'wages': str(wages),
        'federal_withheld': str(fed),
        'note': 'Preparation summary only — not e-filed to IRS',
    }


def generate_ca_t1_prep(tenant, employee, tax_year: int, payslips) -> dict:
    income = sum(p.gross_pay for p in payslips)
    fed = sum(_line_sum(p, 'FED_TAX') for p in payslips)
    return {
        'form': 'T1-prep',
        'tax_year': tax_year,
        'employee': f'{employee.first_name} {employee.last_name}',
        'employment_income': str(income),
        'federal_tax_deducted': str(fed),
        'note': 'Preparation summary only — not e-filed to CRA',
    }


def save_compliance_document(
    tenant_id,
    employee,
    jurisdiction,
    doc_type,
    fy,
    content_bytes,
    metadata=None,
    ext='pdf',
):
    from django.core.files.base import ContentFile

    doc = ComplianceDocument.objects.create(
        tenant_id=tenant_id,
        employee=employee,
        jurisdiction=jurisdiction,
        document_type=doc_type,
        fiscal_year=fy,
        metadata=metadata or {},
    )
    doc.file.save(f'{doc_type}_{employee.employee_code}_{fy}.{ext}', ContentFile(content_bytes))
    doc.save()
    return doc


# Re-export for payroll payslip PDF
_pdf_from_text = pdf_from_text
