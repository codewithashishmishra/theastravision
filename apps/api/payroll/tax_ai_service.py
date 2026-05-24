"""AI-generated personalized tax savings tips for ESS employees."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from core.jurisdictions import currency_for_jurisdiction
from core.models import EnvConfiguration
from employees.models import EmployeeTaxProfile
from payroll.models import Payslip, SalaryStructure, TaxDeclaration
from payroll.services import get_active_rules


def _decimal_str(value) -> str:
    if value is None:
        return '0'
    return str(Decimal(str(value)).quantize(Decimal('0.01')))


def _sanitize_profile_fields(fields: dict) -> dict:
    """Strip tax ID numbers before sending to the LLM."""
    if not fields:
        return {}
    redacted_keys = {'pan_number', 'aadhaar_number', 'ssn', 'sin', 'uan_number', 'pf_number', 'esic_number'}
    return {k: v for k, v in fields.items() if k not in redacted_keys}


def build_employee_tax_context(employee, jurisdiction: str, fiscal_year: int) -> dict:
    employee = (
        type(employee).objects.filter(pk=employee.pk)
        .select_related('branch', 'department', 'designation', 'tenant')
        .first()
    )

    salary = SalaryStructure.objects.filter(employee=employee).first()
    tax_profile_obj = EmployeeTaxProfile.objects.filter(
        employee=employee, jurisdiction=jurisdiction
    ).first()
    declaration_obj = TaxDeclaration.objects.filter(
        employee=employee,
        jurisdiction=jurisdiction,
        fiscal_year=fiscal_year,
    ).first()

    payslips = (
        Payslip.objects.filter(employee=employee, jurisdiction=jurisdiction)
        .select_related('payroll_run')
        .prefetch_related('line_items')
        .order_by('-payroll_run__year', '-payroll_run__month')[:3]
    )

    run_date = date.today()
    rules = get_active_rules(jurisdiction, run_date)
    currency = currency_for_jurisdiction(jurisdiction)

    payslip_summaries = []
    for ps in payslips:
        deductions = {
            li.statutory_code: _decimal_str(li.amount)
            for li in ps.line_items.all()
            if li.item_type == 'Deduction' and not li.is_employer_contribution and li.statutory_code
        }
        payslip_summaries.append({
            'month': ps.payroll_run.month,
            'year': ps.payroll_run.year,
            'gross_pay': _decimal_str(ps.gross_pay),
            'net_pay': _decimal_str(ps.net_pay),
            'total_deductions': _decimal_str(ps.total_deductions),
            'ytd_gross': _decimal_str(ps.ytd_gross),
            'ytd_tax': _decimal_str(ps.ytd_tax),
            'deductions_by_code': deductions,
        })

    branch_state = ''
    if employee.branch:
        branch_state = employee.branch.state or ''

    context = {
        'jurisdiction': jurisdiction,
        'fiscal_year': fiscal_year,
        'currency': currency,
        'employee': {
            'marital_status': employee.marital_status,
            'date_of_joining': str(employee.date_of_joining) if employee.date_of_joining else None,
            'payroll_jurisdiction': employee.payroll_jurisdiction,
            'branch_state_or_province': branch_state,
            'department': employee.department.name if employee.department_id else None,
            'designation': employee.designation.name if employee.designation_id else None,
        },
        'salary_structure': None,
        'tax_profile': _sanitize_profile_fields(tax_profile_obj.fields if tax_profile_obj else {}),
        'tax_declaration': declaration_obj.sections if declaration_obj else {},
        'declaration_status': declaration_obj.status if declaration_obj else None,
        'recent_payslips': payslip_summaries,
        'statutory_rules_summary': _rules_summary(jurisdiction, rules),
    }

    if salary:
        context['salary_structure'] = {
            'annual_ctc': _decimal_str(salary.ctc),
            'monthly_ctc': _decimal_str(Decimal(str(salary.ctc)) / Decimal('12')),
            'components': salary.components or {},
            'variable_pay_enabled': salary.variable_pay_enabled,
            'variable_pay_amount': _decimal_str(salary.variable_pay_amount) if salary.variable_pay_amount else None,
            'variable_pay_pct': str(salary.variable_pay_pct) if salary.variable_pay_pct else None,
        }

    return context


def _rules_summary(jurisdiction: str, rules: dict) -> dict:
    if jurisdiction == 'IN':
        return {
            'pf_wage_ceiling': rules.get('pf_wage_ceiling'),
            'esi_threshold': rules.get('esi_threshold'),
            'section_80c_limit': 150000,
            'tds_slabs_old': rules.get('tds_slabs_old', []),
            'tds_slabs_new': rules.get('tds_slabs_new', []),
        }
    if jurisdiction == 'US':
        return {
            'fica_ss_wage_base': rules.get('fica_ss_wage_base'),
            'federal_brackets': rules.get('federal_brackets', []),
            'state_tax_rates': rules.get('state_tax_rates', {}),
        }
    return {
        'cpp_max_annual': rules.get('cpp_max_annual'),
        'ei_max_annual': rules.get('ei_max_annual'),
        'federal_brackets': rules.get('federal_brackets', []),
        'provincial_brackets_keys': list((rules.get('provincial_brackets') or {}).keys()),
    }


def _get_openai_client():
    cfg = EnvConfiguration.get_cached_config('AI') or {}
    api_key = cfg.get('api_key', '')
    model = cfg.get('model') or 'gpt-5.4-mini'
    provider = cfg.get('provider', 'openai')

    if not api_key:
        raise ValueError(
            'AI is not configured. Add your OpenAI API key under Platform Config → AI settings.'
        )
    if provider != 'openai':
        raise ValueError(f'Unsupported AI provider: {provider}')

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError('openai package is not installed.') from exc

    return OpenAI(api_key=api_key), model


def _jurisdiction_prompt_notes(jurisdiction: str) -> str:
    if jurisdiction == 'IN':
        return (
            'Cover India-specific sections/clauses: 80C, 80D, 80CCD(1B), HRA exemption, '
            'new vs old tax regime comparison, standard deduction, NPS, home loan interest (24b), '
            'PF/ESI where relevant. Use INR amounts from context.'
        )
    if jurisdiction == 'US':
        return (
            'Cover US-specific items: W-4 filing status and withholding, 401(k)/403(b) deferrals, '
            'HSA/FSA, state income tax based on branch_state_or_province, FICA context, '
            'SALT deduction awareness. Use USD amounts from context.'
        )
    return (
        'Cover Canada-specific items: TD1 federal and provincial claims, RRSP contribution room, '
        'TFSA, CPP and EI deductions context, provincial tax credits based on branch province. '
        'Use CAD amounts from context.'
    )


def generate_tax_tips(employee, jurisdiction: str, fiscal_year: int) -> dict:
    context = build_employee_tax_context(employee, jurisdiction, fiscal_year)
    client, model = _get_openai_client()

    jurisdiction_notes = _jurisdiction_prompt_notes(jurisdiction)
    user_prompt = f"""Analyze this employee payroll and tax data and return personalized tax-saving tips.

Jurisdiction: {jurisdiction}
Fiscal/Tax Year: {fiscal_year}

Employee data (JSON):
{json.dumps(context, default=str)}

Requirements:
- {jurisdiction_notes}
- Reference specific numbers from their salary, declarations, and payslips.
- Cite statutory sections/clauses by name (e.g. "Section 80C", "W-4", "TD1", "RRSP").
- Provide 4-8 actionable tips ordered by estimated impact.
- Include regime_comparison only for IN when old vs new regime is relevant; otherwise omit or set null.
- Always include a disclaimer that this is educational only, not legal/tax advice.

Return JSON only with this schema:
{{
  "summary": "2-3 sentence overview tailored to this employee",
  "tips": [
    {{
      "title": "short title",
      "clause": "statutory section or clause name",
      "detail": "detailed explanation using their actual figures",
      "estimated_impact": "qualitative or quantitative savings estimate",
      "action_items": ["concrete step 1", "concrete step 2"]
    }}
  ],
  "regime_comparison": {{ "note": "..." }} or null,
  "disclaimer": "Educational only. Consult a qualified CA/CPA before filing."
}}"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are a tax education assistant for employees in India, the United States, '
                    'and Canada. Provide practical, personalized tax-saving guidance based on payroll '
                    'data. Never provide binding legal advice. Output valid JSON only.'
                ),
            },
            {'role': 'user', 'content': user_prompt},
        ],
        response_format={'type': 'json_object'},
    )
    content = response.choices[0].message.content or '{}'
    data = json.loads(content)
    data.setdefault('summary', '')
    data.setdefault('tips', [])
    data.setdefault(
        'disclaimer',
        'Educational only. Consult a qualified CA/CPA before filing.',
    )
    return data
