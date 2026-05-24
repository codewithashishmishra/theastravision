"""India statutory payroll calculator."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from core.jurisdictions import JURISDICTION_IN, currency_for_jurisdiction
from payroll.engines.base import LineItemResult, PayrollCalcInput, PayrollCalcResult, PayrollCalculator
from payroll.variable_pay import is_variable_pay_enabled, monthly_variable_amount

Q = lambda v: Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _annual_tax_old(annual: Decimal, rules: dict) -> Decimal:
    slabs = rules.get('tds_slabs_old', [])
    tax = Decimal('0')
    remaining = annual
    prev = Decimal('0')
    for slab in slabs:
        upto = Decimal(str(slab['upto'])) if slab['upto'] is not None else None
        rate = Decimal(str(slab['rate']))
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


def _annual_tax_new(annual: Decimal, rules: dict) -> Decimal:
    slabs = rules.get('tds_slabs_new', [])
    tax = Decimal('0')
    remaining = annual
    prev = Decimal('0')
    for slab in slabs:
        upto = Decimal(str(slab['upto'])) if slab['upto'] is not None else None
        rate = Decimal(str(slab['rate']))
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


class IndiaPayrollCalculator(PayrollCalculator):
    jurisdiction = JURISDICTION_IN

    def calculate(self, data: PayrollCalcInput) -> PayrollCalcResult:
        rules = data.rules
        profile = data.tax_profile or {}
        declaration = data.tax_declaration or {}
        components = data.salary_structure.components or {}
        tenant = data.tenant

        monthly_ctc = data.salary_structure.ctc / Decimal('12')
        if data.lop_days:
            monthly_ctc = monthly_ctc * (Decimal('30') - Decimal(str(data.lop_days))) / Decimal('30')

        variable = Decimal('0')
        if tenant and is_variable_pay_enabled(tenant, data.salary_structure):
            variable = Q(monthly_variable_amount(data.salary_structure, monthly_ctc))
            variable = min(variable, monthly_ctc)

        fixed_monthly = monthly_ctc - variable

        basic_pct = Decimal(str(components.get('basic_pct', 0.4)))
        hra_pct = Decimal(str(components.get('hra_pct', 0.2)))
        basic = Q(fixed_monthly * basic_pct)
        hra = Q(fixed_monthly * hra_pct)
        special = Q(fixed_monthly - basic - hra)
        gross = Q(basic + hra + special + variable)

        line_items: list[LineItemResult] = [
            LineItemResult('Basic', 'Earning', basic, 'BASIC'),
            LineItemResult('HRA', 'Earning', hra, 'HRA'),
            LineItemResult('Special Allowance', 'Earning', special, 'SPECIAL'),
        ]
        if variable > 0:
            line_items.append(LineItemResult('Variable Pay', 'Earning', variable, 'VARIABLE'))

        pf_rate = Decimal(str(rules.get('pf_rate', 0.12)))
        pf_ceiling = Decimal(str(rules.get('pf_wage_ceiling', 15000)))
        pf_wage = min(basic, pf_ceiling)
        pf_ee = Q(pf_wage * pf_rate)
        pf_er = Q(pf_wage * pf_rate)
        line_items.append(LineItemResult('PF (Employee)', 'Deduction', pf_ee, 'PF_EE'))
        line_items.append(LineItemResult('PF (Employer)', 'Deduction', pf_er, 'PF_ER', True))

        esi_threshold = Decimal(str(rules.get('esi_threshold', 21000)))
        if gross <= esi_threshold:
            esi_ee = Q(gross * Decimal(str(rules.get('esi_ee_rate', 0.0075))))
            esi_er = Q(gross * Decimal(str(rules.get('esi_er_rate', 0.0325))))
            line_items.append(LineItemResult('ESI (Employee)', 'Deduction', esi_ee, 'ESI_EE'))
            line_items.append(LineItemResult('ESI (Employer)', 'Deduction', esi_er, 'ESI_ER', True))

        state = ''
        if data.employee.branch_id and data.employee.branch:
            state = (data.employee.branch.state or '').strip().lower()
        pt_map = rules.get('pt_by_state', {})
        pt = Q(Decimal(str(pt_map.get(state, pt_map.get('default', 200)))))
        line_items.append(LineItemResult('Professional Tax', 'Deduction', pt, 'PT'))

        lwf_map = rules.get('lwf_by_state', {})
        lwf = Q(Decimal(str(lwf_map.get(state, lwf_map.get('default', 0)))))
        if lwf > 0:
            line_items.append(LineItemResult('Labour Welfare Fund', 'Deduction', lwf, 'LWF'))

        regime = profile.get('tax_regime', 'new')
        annual_gross = gross * Decimal('12')
        deductions_80c = Decimal(str(declaration.get('section_80c', 0)))
        deductions_80d = Decimal(str(declaration.get('section_80d', 0)))
        hra_exempt = Decimal('0')
        if declaration.get('hra_rent_paid'):
            rent = Decimal(str(declaration['hra_rent_paid'])) * Decimal('12')
            hra_exempt = min(hra * Decimal('12'), rent - annual_gross * Decimal('0.1'), hra * Decimal('12'))
        taxable_annual = annual_gross - min(deductions_80c, Decimal('150000')) - deductions_80d - hra_exempt
        if taxable_annual < 0:
            taxable_annual = Decimal('0')

        if regime == 'old':
            annual_tax = _annual_tax_old(taxable_annual, rules)
        else:
            annual_tax = _annual_tax_new(taxable_annual, rules)
        monthly_tds = Q(annual_tax / Decimal('12'))
        line_items.append(LineItemResult('TDS', 'Deduction', monthly_tds, 'TDS'))

        ee_deductions = sum(
            li.amount for li in line_items if li.item_type == 'Deduction' and not li.is_employer_contribution
        )
        net = Q(gross - ee_deductions)
        ytd_gross = Q(data.ytd_gross + gross)
        ytd_tax = Q(data.ytd_tax + monthly_tds)

        return PayrollCalcResult(
            gross_pay=gross,
            total_deductions=ee_deductions,
            net_pay=net,
            line_items=line_items,
            ytd_gross=ytd_gross,
            ytd_tax=ytd_tax,
            currency=currency_for_jurisdiction(JURISDICTION_IN),
        )
