"""Route payroll calculations to jurisdiction-specific calculators."""

from __future__ import annotations

from core.jurisdictions import JURISDICTION_CA, JURISDICTION_IN, JURISDICTION_US
from payroll.engines.base import PayrollCalculator
from payroll.engines.canada import CanadaPayrollCalculator
from payroll.engines.india import IndiaPayrollCalculator
from payroll.engines.united_states import USPayrollCalculator

_CALCULATORS: dict[str, PayrollCalculator] = {
    JURISDICTION_IN: IndiaPayrollCalculator(),
    JURISDICTION_US: USPayrollCalculator(),
    JURISDICTION_CA: CanadaPayrollCalculator(),
}


def get_calculator(jurisdiction: str) -> PayrollCalculator:
    calc = _CALCULATORS.get(jurisdiction)
    if not calc:
        raise ValueError(f'Unsupported payroll jurisdiction: {jurisdiction}')
    return calc
