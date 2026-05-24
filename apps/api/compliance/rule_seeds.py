"""Seed statutory rule sets for IN, US, CA (FY/TY 2025-26)."""

from datetime import date

from compliance.models import StatutoryRuleSet

INDIA_RULES = {
    'pf_rate': 0.12,
    'pf_wage_ceiling': 15000,
    'esi_threshold': 21000,
    'esi_ee_rate': 0.0075,
    'esi_er_rate': 0.0325,
    'tds_slabs_old': [
        {'upto': 250000, 'rate': 0},
        {'upto': 500000, 'rate': 0.05},
        {'upto': 1000000, 'rate': 0.20},
        {'upto': None, 'rate': 0.30},
    ],
    'tds_slabs_new': [
        {'upto': 300000, 'rate': 0},
        {'upto': 700000, 'rate': 0.05},
        {'upto': 1000000, 'rate': 0.10},
        {'upto': 1200000, 'rate': 0.15},
        {'upto': 1500000, 'rate': 0.20},
        {'upto': None, 'rate': 0.30},
    ],
    'pt_by_state': {
        'default': 200,
        'maharashtra': 200,
        'karnataka': 200,
        'telangana': 200,
    },
    'lwf_by_state': {
        'default': 0,
        'maharashtra': 12,
        'karnataka': 20,
    },
}

US_RULES = {
    'fica_ss_rate': 0.062,
    'fica_ss_wage_base': 176100,
    'medicare_rate': 0.0145,
    'medicare_additional_rate': 0.009,
    'medicare_additional_threshold': 200000,
    'futa_rate': 0.006,
    'federal_brackets': [
        {'upto': 11600, 'rate': 0.10},
        {'upto': 47150, 'rate': 0.12},
        {'upto': 100525, 'rate': 0.22},
        {'upto': 191950, 'rate': 0.24},
        {'upto': 243725, 'rate': 0.32},
        {'upto': 609350, 'rate': 0.35},
        {'upto': None, 'rate': 0.37},
    ],
    'state_tax_rates': {
        'CA': 0.05,
        'NY': 0.045,
        'TX': 0,
        'FL': 0,
        'WA': 0,
    },
}

CA_RULES = {
    'cpp_rate': 0.0595,
    'cpp_max_annual': 3867.5,
    'ei_rate': 0.0164,
    'ei_max_annual': 1077.48,
    'federal_brackets': [
        {'upto': 55867, 'rate': 0.15},
        {'upto': 111733, 'rate': 0.205},
        {'upto': 173205, 'rate': 0.26},
        {'upto': 246752, 'rate': 0.29},
        {'upto': None, 'rate': 0.33},
    ],
    'provincial_brackets': {
        'ON': [
            {'upto': 51446, 'rate': 0.0505},
            {'upto': 102894, 'rate': 0.0915},
            {'upto': 150000, 'rate': 0.1116},
            {'upto': 220000, 'rate': 0.1216},
            {'upto': None, 'rate': 0.1316},
        ],
        'BC': [
            {'upto': 47937, 'rate': 0.0506},
            {'upto': 95875, 'rate': 0.077},
            {'upto': 110076, 'rate': 0.105},
            {'upto': 133664, 'rate': 0.1229},
            {'upto': 181232, 'rate': 0.147},
            {'upto': None, 'rate': 0.168},
        ],
    },
}


def seed_statutory_rules():
    effective = date(2025, 4, 1)
    sets = [
        ('IN', 'FY2025-26', INDIA_RULES),
        ('US', 'TY2025', US_RULES),
        ('CA', 'TY2025', CA_RULES),
    ]
    for jurisdiction, version, rules in sets:
        StatutoryRuleSet.objects.update_or_create(
            jurisdiction=jurisdiction,
            version=version,
            defaults={
                'effective_from': effective,
                'effective_to': None,
                'rules': rules,
            },
        )
