"""Variable pay resolution for India and other jurisdictions."""

from __future__ import annotations

from decimal import Decimal


def is_variable_pay_enabled(tenant, salary_structure) -> bool:
    if not tenant.variable_pay_enabled:
        return False
    if not tenant.allow_employee_variable_override:
        return True
    if salary_structure.variable_pay_enabled is not None:
        return bool(salary_structure.variable_pay_enabled)
    return True


def monthly_variable_amount(salary_structure, monthly_ctc: Decimal) -> Decimal:
    if salary_structure.variable_pay_amount is not None:
        return Decimal(str(salary_structure.variable_pay_amount))
    if salary_structure.variable_pay_pct is not None:
        return monthly_ctc * Decimal(str(salary_structure.variable_pay_pct))
    components = salary_structure.components or {}
    if components.get('variable_pct') is not None:
        return monthly_ctc * Decimal(str(components['variable_pct']))
    return Decimal('0')
