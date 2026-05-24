"""United States payroll calculator."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from core.jurisdictions import JURISDICTION_US, currency_for_jurisdiction
from payroll.engines.base import LineItemResult, PayrollCalcInput, PayrollCalcResult, PayrollCalculator

Q = lambda v: Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _federal_withholding(monthly_gross: Decimal, profile: dict, rules: dict) -> Decimal:
    annual = monthly_gross * Decimal('12')
    brackets = rules.get('federal_brackets', [])
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

    filing = profile.get('w4_filing_status', 'single')
    if filing == 'married':
        tax *= Decimal('0.92')
    elif filing == 'head_of_household':
        tax *= Decimal('0.88')

    extra = Decimal(str(profile.get('w4_extra_withholding', 0))) * Decimal('12')
    return Q((tax + extra) / Decimal('12'))


class USPayrollCalculator(PayrollCalculator):
    jurisdiction = JURISDICTION_US

    def calculate(self, data: PayrollCalcInput) -> PayrollCalcResult:
        rules = data.rules
        profile = data.tax_profile or {}
        monthly_gross = Q(data.salary_structure.ctc / Decimal('12'))
        if data.lop_days:
            monthly_gross = Q(monthly_gross * (Decimal('30') - Decimal(str(data.lop_days))) / Decimal('30'))

        line_items: list[LineItemResult] = [
            LineItemResult('Gross Pay', 'Earning', monthly_gross, 'GROSS'),
        ]

        ss_rate = Decimal(str(rules.get('fica_ss_rate', 0.062)))
        ss_base = Decimal(str(rules.get('fica_ss_wage_base', 176100)))
        ytd_gross = data.ytd_gross + monthly_gross
        ss_wages = min(monthly_gross, max(Decimal('0'), ss_base - data.ytd_gross))
        fica_ss = Q(ss_wages * ss_rate)
        line_items.append(LineItemResult('Social Security', 'Deduction', fica_ss, 'FICA_SS'))

        medicare_rate = Decimal(str(rules.get('medicare_rate', 0.0145)))
        medicare = Q(monthly_gross * medicare_rate)
        addl_threshold = Decimal(str(rules.get('medicare_additional_threshold', 200000)))
        if ytd_gross > addl_threshold:
            medicare += Q(monthly_gross * Decimal(str(rules.get('medicare_additional_rate', 0.009))))
        line_items.append(LineItemResult('Medicare', 'Deduction', medicare, 'FICA_MED'))

        federal = _federal_withholding(monthly_gross, profile, rules)
        line_items.append(LineItemResult('Federal Income Tax', 'Deduction', federal, 'FED_WH'))

        state_code = ''
        if data.employee.branch_id and data.employee.branch:
            state_code = (data.employee.branch.state or '').strip().upper()
        state_rates = rules.get('state_tax_rates', {})
        state_rate = Decimal(str(state_rates.get(state_code, 0)))
        state_tax = Q(monthly_gross * state_rate)
        if state_tax > 0:
            line_items.append(LineItemResult(f'State Tax ({state_code})', 'Deduction', state_tax, 'STATE_WH'))

        futa_rate = Decimal(str(rules.get('futa_rate', 0.006)))
        futa = Q(monthly_gross * futa_rate)
        line_items.append(LineItemResult('FUTA (Employer)', 'Deduction', futa, 'FUTA', True))

        ee_deductions = sum(
            li.amount for li in line_items if li.item_type == 'Deduction' and not li.is_employer_contribution
        )
        total_tax = federal + state_tax + fica_ss + medicare
        return PayrollCalcResult(
            gross_pay=monthly_gross,
            total_deductions=ee_deductions,
            net_pay=Q(monthly_gross - ee_deductions),
            line_items=line_items,
            ytd_gross=Q(ytd_gross),
            ytd_tax=Q(data.ytd_tax + total_tax),
            currency=currency_for_jurisdiction(JURISDICTION_US),
        )
