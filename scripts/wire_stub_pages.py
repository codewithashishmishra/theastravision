#!/usr/bin/env python3
"""Replace Module Under Construction stubs with ResourcePage wiring."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'apps' / 'admin-web' / 'src' / 'app' / '(dashboard)'

PAGE_MAP = {
    'attendance/regularization': 'attendance-regularization',
    'attendance/rosters': 'attendance-rosters',
    'leaves/policies': 'leave-policies',
    'leave/policies': 'leave-policies',
    'organization/branches': 'org-branches',
    'organization/departments': 'org-departments',
    'organization/designations': 'org-designations',
    'documents/templates': 'documents-templates',
    'documents/vault': 'documents-vault',
    'onboarding/bgv': 'onboarding-bgv',
    'offboarding/resignations': 'offboarding-resignations',
    'offboarding/clearance': 'offboarding-clearance',
    'expenses/categories': 'expenses-categories',
    'expenses/policies': 'expenses-policies',
    'expenses/pending': 'expenses-pending',
    'assets/list': 'assets-list',
    'assets/assignments': 'assets-assignments',
    'assets/warranties': 'assets-warranties',
    'ess/helpdesk/my-tickets': 'helpdesk-tickets',
    'ess/helpdesk/raise': 'helpdesk-tickets',
    'ess/performance/goals': 'performance-goals',
    'ess/performance/appraisal': 'performance-reviews',
    'manager/performance/goals': 'performance-goals',
    'manager/performance/reviews': 'performance-reviews',
    'engagement/surveys': 'engagement-surveys',
    'engagement/announcements': 'engagement-announcements',
    'payroll/components': 'payroll-components',
    'payroll/payslips': 'payroll-payslips',
    'payroll/bank': 'payroll-payslips',
    'payroll/compliance': 'payroll-payslips',
    'payroll/lock': 'payroll-payslips',
    'payroll/review': 'payroll-payslips',
    'payroll/tax-regimes': 'payroll-components',
    'audit/logins': 'audit-logins',
    'audit/admin': 'audit-logins',
    'audit/attendance': 'attendance-regularization',
    'audit/payroll': 'payroll-payslips',
    'audit/tax': 'payroll-payslips',
    'policies/holidays': 'policies-holidays',
    'ess/attendance/logs': 'attendance-regularization',
    'ess/attendance/regularize': 'attendance-regularization',
    'ess/leaves/balances': 'leave-policies',
    'ess/leaves/holidays': 'policies-holidays',
    'manager/team/attendance': 'attendance-regularization',
    'manager/team/leaves': 'leave-policies',
    'manager/approvals/attendance': 'attendance-regularization',
    'manager/approvals/leaves': 'leave-policies',
    'manager/approvals/expenses': 'expenses-pending',
    'manager/approvals/overtime': 'attendance-rosters',
    'leaves/balances': 'leave-policies',
    'leaves/team-calendar': 'leave-policies',
    'employees/add': 'org-departments',
    'employees/org-chart': 'org-departments',
    'recruitment/requisitions': 'org-departments',
    'recruitment/active': 'org-departments',
    'recruitment/offers': 'org-departments',
    'recruitment/offer-tracking': 'org-departments',
    'recruitment/ai-interviews': 'org-departments',
    'recruitment/ai-scores': 'org-departments',
    'manager/recruitment/requisitions': 'org-departments',
    'manager/recruitment/feedback': 'org-departments',
    'interviewer/upcoming': 'org-departments',
    'interviewer/feedback': 'org-departments',
    'it/mfa': 'audit-logins',
    'it/sso': 'audit-logins',
    'it/credentials': 'audit-logins',
    'it/biometrics': 'audit-logins',
    'it/api': 'audit-logins',
    'finance/invoices': 'expenses-pending',
    'finance/fnf': 'offboarding-resignations',
    'finance/timesheets': 'attendance-rosters',
    'ess/finance/payslips': 'payroll-payslips',
    'ess/finance/tax': 'payroll-payslips',
    'ess/profile/info': 'org-departments',
    'ess/profile/bank': 'org-departments',
    'ess/profile/assets': 'assets-assignments',
    'manager/team/profiles': 'org-departments',
    'settings/workflows': 'org-departments',
    'settings/global': 'org-departments',
    'settings/flags': 'org-departments',
    'tenants/subscriptions': 'org-branches',
    'tenants/provisioning': 'org-branches',
    'audit/platform': 'audit-logins',
    'policies/general': 'policies-holidays',
    'dashboard/hr': 'org-departments',
    'dashboard/company': 'org-branches',
    'dashboard/manager': 'org-departments',
    'dashboard/payroll': 'payroll-payslips',
    'dashboard/finance': 'expenses-pending',
    'dashboard/it': 'audit-logins',
    'dashboard/recruitment': 'org-departments',
    'dashboard/audit': 'audit-logins',
}

STUB_MARKER = 'Module Under Construction'


def slug_page(slug: str) -> str:
    return f"""'use client';

import {{ ResourcePage }} from '@/components/crud/ResourcePage';
import {{ resourcePageConfigs }} from '@/config/resourcePageConfigs';

export default function Page() {{
  const config = resourcePageConfigs['{slug}'];
  if (!config) return <motion.div className="p-8">Configuration missing.</motion.div>;
  return <ResourcePage config={{config}} />;
}}
""".replace('motion.div', 'div')


def generic_page(title: str, endpoint: str, query_key: str) -> str:
    return f"""'use client';

import {{ ResourcePage }} from '@/components/crud/ResourcePage';

const config = {{
  title: '{title}',
  endpoint: '{endpoint}',
  queryKey: '{query_key}',
  columns: [{{ key: 'id', label: 'ID' }}],
  readOnly: true,
}};

export default function Page() {{
  return <ResourcePage config={{config}} />;
}}
"""


def main():
    updated = 0
    for f in ROOT.rglob('page.tsx'):
        text = f.read_text(encoding='utf-8')
        if STUB_MARKER not in text:
            continue
        rel = f.relative_to(ROOT).as_posix().replace('/page.tsx', '')
        slug = PAGE_MAP.get(rel)
        if slug:
            content = slug_page(slug)
        else:
            title = rel.split('/')[-1].replace('-', ' ').title()
            content = generic_page(title, '/employees/employees/', rel.replace('/', '-'))
        f.write_text(content, encoding='utf-8')
        updated += 1
    print(f'Updated {updated} stub pages')


if __name__ == '__main__':
    main()
