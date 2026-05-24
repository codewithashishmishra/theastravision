"""Payroll run orchestration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from compliance.models import StatutoryRuleSet
from employees.models import EmployeeTaxProfile
from payroll.engines.base import PayrollCalcInput
from payroll.engines.router import get_calculator
from payroll.models import PayrollLineItem, PayrollRun, Payslip, SalaryStructure, TaxDeclaration


def get_active_rules(jurisdiction: str, run_date: date) -> dict:
    rule_set = (
        StatutoryRuleSet.objects.filter(
            jurisdiction=jurisdiction,
            effective_from__lte=run_date,
        )
        .filter(models_q_effective_to(run_date))
        .order_by('-effective_from')
        .first()
    )
    return rule_set.rules if rule_set else {}


def models_q_effective_to(run_date: date):
    from django.db.models import Q
    return Q(effective_to__isnull=True) | Q(effective_to__gte=run_date)


def fiscal_year_for_run(run: PayrollRun, tenant) -> int:
    start_month = tenant.fiscal_year_start_month if tenant else 4
    if run.month >= start_month:
        return run.year
    return run.year - 1


def get_ytd_totals(employee, jurisdiction: str, run: PayrollRun) -> tuple[Decimal, Decimal]:
    prior = Payslip.objects.filter(
        employee=employee,
        jurisdiction=jurisdiction,
        payroll_run__year=run.year,
        payroll_run__month__lt=run.month,
    )
    ytd_gross = sum((p.gross_pay for p in prior), Decimal('0'))
    ytd_tax = sum((p.ytd_tax for p in prior), Decimal('0'))
    return ytd_gross, ytd_tax


def generate_payslips_for_run(run: PayrollRun, tenant) -> int:
    from django.db import transaction

    calculator = get_calculator(run.jurisdiction)
    run_date = date(run.year, run.month, 1)
    rules = get_active_rules(run.jurisdiction, run_date)
    fy = fiscal_year_for_run(run, tenant)

    employees_qs = SalaryStructure.objects.filter(
        tenant_id=run.tenant_id,
        employee__payroll_jurisdiction=run.jurisdiction,
        employee__status='Active',
    ).select_related('employee', 'employee__branch')

    if run.legal_entity_id:
        employees_qs = employees_qs.filter(employee__legal_entity_id=run.legal_entity_id)

    created = 0
    with transaction.atomic():
        for structure in employees_qs:
            employee = structure.employee
            tax_profile_obj = EmployeeTaxProfile.objects.filter(
                employee=employee, jurisdiction=run.jurisdiction
            ).first()
            tax_profile = tax_profile_obj.fields if tax_profile_obj else {}

            declaration_obj = TaxDeclaration.objects.filter(
                employee=employee,
                jurisdiction=run.jurisdiction,
                fiscal_year=fy,
            ).first()
            declaration = declaration_obj.sections if declaration_obj else {}

            ytd_gross, ytd_tax = get_ytd_totals(employee, run.jurisdiction, run)
            calc_input = PayrollCalcInput(
                employee=employee,
                salary_structure=structure,
                payroll_run=run,
                rules=rules,
                tax_profile=tax_profile,
                tax_declaration=declaration,
                ytd_gross=ytd_gross,
                ytd_tax=ytd_tax,
                tenant=tenant,
            )
            result = calculator.calculate(calc_input)

            payslip, was_created = Payslip.objects.update_or_create(
                tenant_id=run.tenant_id,
                payroll_run=run,
                employee=employee,
                defaults={
                    'jurisdiction': run.jurisdiction,
                    'currency': result.currency,
                    'gross_pay': result.gross_pay,
                    'total_deductions': result.total_deductions,
                    'net_pay': result.net_pay,
                    'ytd_gross': result.ytd_gross,
                    'ytd_tax': result.ytd_tax,
                    'is_released': False,
                },
            )
            if was_created:
                created += 1

            PayrollLineItem.objects.filter(payslip=payslip).delete()
            for item in result.line_items:
                PayrollLineItem.objects.create(
                    tenant_id=run.tenant_id,
                    payslip=payslip,
                    name=item.name,
                    item_type=item.item_type,
                    amount=item.amount,
                    statutory_code=item.statutory_code,
                    is_employer_contribution=item.is_employer_contribution,
                )

    return created
