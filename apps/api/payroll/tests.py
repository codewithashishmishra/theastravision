"""Payroll calculator and variable pay tests."""

from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase

from compliance.pdf_fill import fill_government_pdf, pdf_from_text
from compliance.rule_seeds import INDIA_RULES, US_RULES, CA_RULES
from payroll.engines.base import PayrollCalcInput
from payroll.engines.india import IndiaPayrollCalculator
from payroll.engines.united_states import USPayrollCalculator
from payroll.engines.canada import CanadaPayrollCalculator
from payroll.variable_pay import is_variable_pay_enabled, monthly_variable_amount


def _employee(branch_state='maharashtra', branch_country='India'):
    branch = SimpleNamespace(state=branch_state, country=branch_country)
    return SimpleNamespace(branch=branch, branch_id='1')


def _structure(ctc='1200000', components=None, **kwargs):
    return SimpleNamespace(
        ctc=Decimal(ctc),
        components=components or {'basic_pct': 0.4, 'hra_pct': 0.2},
        variable_pay_enabled=kwargs.get('variable_pay_enabled'),
        variable_pay_amount=kwargs.get('variable_pay_amount'),
        variable_pay_pct=kwargs.get('variable_pay_pct'),
    )


def _tenant(variable_pay_enabled=False, allow_employee_variable_override=True):
    return SimpleNamespace(
        variable_pay_enabled=variable_pay_enabled,
        allow_employee_variable_override=allow_employee_variable_override,
    )


class VariablePayTests(TestCase):
    def test_variable_pay_disabled_by_default(self):
        tenant = _tenant(False)
        structure = _structure(variable_pay_enabled=True)
        self.assertFalse(is_variable_pay_enabled(tenant, structure))

    def test_variable_pay_enabled_with_amount(self):
        tenant = _tenant(True)
        structure = _structure(variable_pay_enabled=True, variable_pay_amount=Decimal('10000'))
        self.assertTrue(is_variable_pay_enabled(tenant, structure))
        monthly_ctc = Decimal('100000')
        self.assertEqual(monthly_variable_amount(structure, monthly_ctc), Decimal('10000'))

    def test_india_includes_variable_line(self):
        calc = IndiaPayrollCalculator()
        result = calc.calculate(
            PayrollCalcInput(
                employee=_employee(),
                salary_structure=_structure(variable_pay_amount=Decimal('5000'), variable_pay_enabled=True),
                payroll_run=SimpleNamespace(month=5, year=2025),
                rules=INDIA_RULES,
                tax_profile={'tax_regime': 'new'},
                tax_declaration={},
                tenant=_tenant(True),
            )
        )
        codes = {li.statutory_code for li in result.line_items}
        self.assertIn('VARIABLE', codes)


class IndiaCalculatorTests(TestCase):
    def test_india_pf_tds_deductions(self):
        calc = IndiaPayrollCalculator()
        result = calc.calculate(
            PayrollCalcInput(
                employee=_employee(),
                salary_structure=_structure(),
                payroll_run=SimpleNamespace(month=5, year=2025),
                rules=INDIA_RULES,
                tax_profile={'tax_regime': 'new'},
                tax_declaration={'section_80c': 50000},
                tenant=_tenant(False),
            )
        )
        self.assertEqual(result.currency, 'INR')
        self.assertGreater(result.gross_pay, Decimal('0'))
        codes = {li.statutory_code for li in result.line_items}
        self.assertIn('PF_EE', codes)
        self.assertIn('TDS', codes)


class USCalculatorTests(TestCase):
    def test_us_fica_and_federal(self):
        calc = USPayrollCalculator()
        result = calc.calculate(
            PayrollCalcInput(
                employee=_employee(branch_state='CA', branch_country='USA'),
                salary_structure=_structure('96000'),
                payroll_run=SimpleNamespace(month=5, year=2025),
                rules=US_RULES,
                tax_profile={'w4_filing_status': 'single'},
                tax_declaration={},
            )
        )
        self.assertEqual(result.currency, 'USD')
        codes = {li.statutory_code for li in result.line_items}
        self.assertIn('FICA_SS', codes)
        self.assertIn('FED_WH', codes)


class CanadaCalculatorTests(TestCase):
    def test_canada_cpp_ei(self):
        calc = CanadaPayrollCalculator()
        result = calc.calculate(
            PayrollCalcInput(
                employee=_employee(branch_state='ON', branch_country='Canada'),
                salary_structure=_structure('72000'),
                payroll_run=SimpleNamespace(month=5, year=2025),
                rules=CA_RULES,
                tax_profile={},
                tax_declaration={'td1_federal_claim': 15705},
            )
        )
        self.assertEqual(result.currency, 'CAD')
        codes = {li.statutory_code for li in result.line_items}
        self.assertIn('CPP', codes)
        self.assertIn('EI', codes)


class PdfFillTests(TestCase):
    def test_html_fallback_generates_pdf(self):
        pdf, meta = fill_government_pdf(
            'IN',
            'FORM16',
            2025,
            {},
            ['Line 1', 'Line 2'],
            'Form 16',
        )
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertEqual(meta['fill_strategy'], 'html_fallback')

    def test_pdf_from_text(self):
        data = pdf_from_text('Test', ['Hello'])
        self.assertTrue(data.startswith(b'%PDF'))
