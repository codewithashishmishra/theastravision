"""Payroll jurisdiction constants and helpers."""

from __future__ import annotations

JURISDICTION_IN = 'IN'
JURISDICTION_US = 'US'
JURISDICTION_CA = 'CA'

JURISDICTION_CHOICES = [
    (JURISDICTION_IN, 'India'),
    (JURISDICTION_US, 'United States'),
    (JURISDICTION_CA, 'Canada'),
]

JURISDICTION_CURRENCY = {
    JURISDICTION_IN: 'INR',
    JURISDICTION_US: 'USD',
    JURISDICTION_CA: 'CAD',
}

JURISDICTION_FISCAL_START_MONTH = {
    JURISDICTION_IN: 4,
    JURISDICTION_US: 1,
    JURISDICTION_CA: 1,
}

# Map branch country names (lowercase) to payroll jurisdiction codes.
COUNTRY_TO_JURISDICTION = {
    'india': JURISDICTION_IN,
    'in': JURISDICTION_IN,
    'united states': JURISDICTION_US,
    'usa': JURISDICTION_US,
    'us': JURISDICTION_US,
    'canada': JURISDICTION_CA,
    'ca': JURISDICTION_CA,
}


def normalize_jurisdiction(code: str | None) -> str | None:
    if not code:
        return None
    upper = code.strip().upper()
    if upper in {JURISDICTION_IN, JURISDICTION_US, JURISDICTION_CA}:
        return upper
    return None


def jurisdiction_from_country(country: str | None) -> str:
    if not country:
        return JURISDICTION_IN
    return COUNTRY_TO_JURISDICTION.get(country.strip().lower(), JURISDICTION_IN)


def currency_for_jurisdiction(jurisdiction: str) -> str:
    return JURISDICTION_CURRENCY.get(jurisdiction, 'INR')


def fiscal_start_month_for_jurisdiction(jurisdiction: str) -> int:
    return JURISDICTION_FISCAL_START_MONTH.get(jurisdiction, 1)


def default_currency_for_jurisdictions(jurisdictions: list[str]) -> str:
    if not jurisdictions:
        return 'INR'
    return currency_for_jurisdiction(jurisdictions[0])
