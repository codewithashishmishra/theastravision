# Module 6 — Payroll (Multi-Jurisdiction)

## Overview

Payroll supports **India (IN)**, **United States (US)**, and **Canada (CA)**. Employees have `payroll_jurisdiction`; tenants enable jurisdictions and optional **variable pay** (India-first, per-employee override including self-service via linked employee record).

## Official form template URLs

Re-download annually via:

```bash
cd apps/api
python manage.py download_form_templates
python manage.py inspect_form_fields W2 --jurisdiction US
python manage.py inspect_form_fields W2 --jurisdiction US --write-cache
```

**Dynamic field mapping:** AcroForm paths are resolved automatically from each downloaded PDF (semantic segments like `Box1_ReadOrder`, `Col_Left.f2_02`). Maps are cached in `field_maps/{jurisdiction}/{form}_{year}.json` and refreshed when the template file changes (mtime). No manual `f1_1[0]` edits required when IRS publishes a new W-2.

| Region | Document | Source |
|--------|----------|--------|
| IN | Form 16 | https://www.incometax.gov.in/iec/foportal/help/statutory-forms/form-16 |
| IN | Form 12BA | https://www.incometax.gov.in/iec/foportal/help/statutory-forms/form-12ba |
| US | W-2 PDF | https://www.irs.gov/pub/irs-pdf/fw2.pdf |
| US | 1095-C PDF | https://www.irs.gov/pub/irs-pdf/f1095c.pdf |
| CA | T4 | https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/t4.html |
| CA | RL-1 | https://www.revenuquebec.ca/en/businesses/source-deductions-pension-plans/file-returns-amounts-paid/rl-1-slip/ |

Registry: `apps/api/compliance/data/form_registry.json`  
Field maps: `apps/api/compliance/field_maps/{jurisdiction}/`  
Templates: `apps/api/compliance/templates/forms/` (after download)

**Fill strategy:** `acroform` when IRS/CRA PDF fields match; otherwise `html_fallback` (structured PDF via PyMuPDF).

## Variable pay (India)

- **Tenant:** `variable_pay_enabled`, `allow_employee_variable_override`
- **SalaryStructure:** `variable_pay_enabled` (null = inherit), `variable_pay_amount`, `variable_pay_pct`
- Admin: `/payroll/settings`, `/payroll/structures`
- Engine: separate `VARIABLE` earning line; TDS includes variable in gross

## API endpoints

- `GET/PATCH /api/v1/payroll/settings/` — tenant payroll policy
- `POST /api/v1/payroll/runs/{id}/generate|approve|lock|release/`
- `GET /api/v1/payroll/payslips/{id}/pdf/`
- `GET /api/v1/payroll/tax-tips/credits/` — ESS AI tax tips quota (3/month per employee)
- `POST /api/v1/payroll/tax-tips/generate/` — personalized tax-saving tips (IN/US/CA)
- `POST /api/v1/compliance/actions/form16|form12ba|w2|1095c|t4|rl1/generate/`
- `POST /api/v1/compliance/actions/bulk-year-end/` — Celery task

## ESS AI tax tips

Employees (`/ess/finance/tax`) can request **AI Tax Savings Tips** personalized from salary structure, tax declarations, tax profile, and recent payslips.

- **Model:** Platform Config → AI (`gpt-5.4-mini` default)
- **Quota:** 3 requests per employee per calendar month
- **Jurisdictions:** IN (80C, HRA, regime), US (W-4, 401k, state), CA (TD1, RRSP, CPP/EI)
- **Disclaimer:** Educational only — not legal or tax advice; consult a CA/CPA before filing

## Seed commands

```bash
python manage.py seed_statutory_rules
python manage.py migrate
```

## Tests

```bash
python manage.py test payroll compliance
```

## Disclaimer

Generated forms are employer summaries. No direct e-filing to TRACES, IRS, or CRA in v1.
