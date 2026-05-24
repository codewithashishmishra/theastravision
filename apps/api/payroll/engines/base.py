"""Payroll calculator strategy pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class LineItemResult:
    name: str
    item_type: str
    amount: Decimal
    statutory_code: str = ''
    is_employer_contribution: bool = False


@dataclass
class PayrollCalcResult:
    gross_pay: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    line_items: list[LineItemResult] = field(default_factory=list)
    ytd_gross: Decimal = Decimal('0')
    ytd_tax: Decimal = Decimal('0')
    currency: str = 'INR'


@dataclass
class PayrollCalcInput:
    employee: Any
    salary_structure: Any
    payroll_run: Any
    rules: dict
    tax_profile: dict
    tax_declaration: dict
    ytd_gross: Decimal = Decimal('0')
    ytd_tax: Decimal = Decimal('0')
    lop_days: int = 0
    tenant: Any = None


class PayrollCalculator(ABC):
    jurisdiction: str

    @abstractmethod
    def calculate(self, data: PayrollCalcInput) -> PayrollCalcResult:
        pass
