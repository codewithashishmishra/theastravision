"""Canada payroll calculator."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from core.jurisdictions import JURISDICTION_CA, currency_for_jurisdiction
from payroll.engines.base import LineItemResult, PayrollCalcInput, PayrollCalcResult, PayrollCalculator

Q = lambda v: Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _progressive_tax(annual: Decimal, brackets: list) -> Decimal:
    tax = Decimal('0')
    remaining = annual
    prev = Decimal('0')
    for bracket in brackets:
        upto = Decimal(str(bracket['upto'])) if bracket['upto'] is not None else None
        rate = Decimal(str(bracket['rate']))
        if upto is None:
            tax += remaining * rate
            break
        band = min(remaining, upto - prev)
        if band <= 0:
            break
        tax += band * rate
        remaining -= band
        prev = upto
    return tax


class CanadaPayrollCalculator(PayrollCalculator):
    jurisdiction = JURISDICTION_CA

    def calculate(self, data: PayrollCalcInput) -> PayrollCalcResult:
        rules = data.rules
        profile = data.tax_profile or {}
        declaration = data.tax_declaration or {}
        monthly_gross = Q(data.salary_structure.ctc / Decimal('12'))
        if data.lop_days:
            monthly_gross = Q(monthly_gross * (Decimal('30') - Decimal(str(data.lop_days))) / Decimal('30'))

        line_items: list[LineItemResult] = [
            LineItemResult('Gross Pay', 'Earning', monthly_gross, 'GROSS'),
        ]

        cpp_rate = Decimal(str(rules.get('cpp_rate', 0.0595)))
        cpp_max = Decimal(str(rules.get('cpp_max_annual', 3867.5)))
        ytd_gross = data.ytd_gross + monthly_gross
        cpp_ytd_cap = cpp_max
        cpp_room = max(Decimal('0'), cpp_ytd_cap - data.ytd_tax)
        cpp = Q(min(monthly_gross * cpp_rate, cpp_room))
        line_items.append(LineItemResult('CPP', 'Deduction', cpp, 'CPP'))

        ei_rate = Decimal(str(rules.get('ei_rate', 0.0164)))
        ei_max = Decimal(str(rules.get('ei_max_annual', 1077.48)))
        ei = Q(min(monthly_gross * ei_rate, ei_max / Decimal('12')))
        line_items.append(LineItemResult('EI', 'Deduction', ei, 'EI'))

        annual_gross = monthly_gross * Decimal('12')
        federal_claim = Decimal(str(declaration.get('td1_federal_claim', profile.get('td1_federal_claim', 15705))))
        federal_taxable = max(Decimal('0'), annual_gross - federal_claim)
        federal_annual = _progressive_tax(federal_taxable, rules.get('federal_brackets', []))
        federal = Q(federal_annual / Decimal('12'))
        line_items.append(LineItemResult('Federal Income Tax', 'Deduction', federal, 'FED_TAX'))

        province = ''
        if data.employee.branch_id and data.employee.branch:
            province = (data.employee.branch.state or '').strip().upper()
        prov_brackets = rules.get('provincial_brackets', {}).get(province, rules.get('provincial_brackets', {}).get('ON', []))
        prov_claim = Decimal(str(declaration.get('td1_provincial_claim', profile.get('td1_provincial_claim', 11865))))
        prov_taxable = max(Decimal('0'), annual_gross - prov_claim)
        prov_annual = _progressive_tax(prov_taxable, prov_brackets)
        provincial = Q(prov_annual / Decimal('12'))
        if provincial > 0:
            line_items.append(LineItemResult(f'Provincial Tax ({province or "ON"})', 'Deduction', provincial, 'PROV_TAX'))

        ee_deductions = sum(
            li.amount for li in line_items if li.item_type == 'Deduction' and not li.is_employer_contribution
        )
        total_tax = federal + provincial + cpp + ei
        return PayrollCalcResult(
            gross_pay=monthly_gross,
            total_deductions=ee_deductions,
            net_pay=Q(monthly_gross - ee_deductions),
            line_items=line_items,
            ytd_gross=Q(ytd_gross),
            ytd_tax=Q(data.ytd_tax + total_tax),
            currency=currency_for_jurisdiction(JURISDICTION_CA),
        )
