import { 
  LayoutDashboard, Users, Building, Settings, FileText,
  Calendar, CheckSquare, Clock, UsersRound, Globe, FileKey,
  Briefcase, Receipt, ShieldCheck, HelpCircle, Target, FilePlus,
  LogOut, ClipboardList, HandCoins, MonitorCheck, BookOpen, UserPlus, Fingerprint, PieChart, BadgeIndianRupee, Stethoscope, Mail, Activity
} from 'lucide-react';

export type Role = 'Super Admin' | 'Company Admin' | 'HR Admin' | 'Payroll Admin' | 'Finance Admin' | 'IT Admin' | 'Manager' | 'Recruiter' | 'Interviewer' | 'Auditor' | 'Employee';
export const ALL_ROLES: Role[] = ['Super Admin', 'Company Admin', 'HR Admin', 'Payroll Admin', 'Finance Admin', 'IT Admin', 'Manager', 'Recruiter', 'Interviewer', 'Auditor', 'Employee'];

import type { Jurisdiction } from '@/lib/jurisdiction';

export type MenuItem = {
  key: string;
  label: string;
  path?: string;
  icon?: any;
  allowedRoles: Role[];
  jurisdictions?: Jurisdiction[];
  children?: MenuItem[];
};

export type MenuSection = {
  section: string;
  items: MenuItem[];
};

/** Pinned at bottom of sidebar — not included in scrollable menuConfig sections. */
export const profileNavItem: MenuItem = {
  key: 'ess-profile',
  label: 'My Profile',
  icon: UserPlus,
  allowedRoles: ALL_ROLES,
  children: [
    { key: 'prof-info', label: 'Personal Info', path: '/ess/profile/info', allowedRoles: ALL_ROLES },
    { key: 'prof-bank', label: 'Bank Details', path: '/ess/profile/bank', allowedRoles: ALL_ROLES },
    { key: 'prof-assets', label: 'My Assets', path: '/ess/profile/assets', allowedRoles: ALL_ROLES },
    { key: 'prof-work-location', label: 'Work Location', path: '/ess/profile/work-location', allowedRoles: ALL_ROLES },
  ],
};

/** Account settings — all authenticated roles (not platform config). */
export const accountSettingsNavItem: MenuItem = {
  key: 'account-settings',
  label: 'Account Settings',
  path: '/settings/account',
  icon: Settings,
  allowedRoles: ALL_ROLES,
};

export const menuConfig: MenuSection[] = [
  {
    section: 'Dashboards',
    items: [
      { key: 'platform-dash', label: 'Platform Dashboard', path: '/dashboards/platform', icon: LayoutDashboard, allowedRoles: ['Super Admin'] },
      { key: 'company-dash', label: 'Company Dashboard', path: '/dashboards/company', icon: LayoutDashboard, allowedRoles: ['Company Admin'] },
      { key: 'hr-dash', label: 'HR Dashboard', path: '/dashboards/hr', icon: LayoutDashboard, allowedRoles: ['HR Admin'] },
      { key: 'payroll-dash', label: 'Payroll Dashboard', path: '/dashboards/payroll', icon: LayoutDashboard, allowedRoles: ['Payroll Admin'] },
      { key: 'finance-dash', label: 'Finance Dashboard', path: '/dashboards/finance', icon: LayoutDashboard, allowedRoles: ['Finance Admin'] },
      { key: 'it-dash', label: 'IT Dashboard', path: '/dashboards/it', icon: LayoutDashboard, allowedRoles: ['IT Admin'] },
      { key: 'manager-dash', label: 'Manager Dashboard', path: '/dashboards/manager', icon: LayoutDashboard, allowedRoles: ['Manager'] },
      { key: 'recruitment-dash', label: 'Recruitment Dashboard', path: '/dashboards/recruitment', icon: LayoutDashboard, allowedRoles: ['Recruiter'] },
      { key: 'audit-dash', label: 'Audit Dashboard', path: '/dashboards/audit', icon: LayoutDashboard, allowedRoles: ['Auditor'] },
      { key: 'employee-dash', label: 'Employee', path: '/dashboards/employee', icon: LayoutDashboard, allowedRoles: ['Employee'] },
    ]
  },
  {
    section: 'Super Admin Operations',
    items: [
      {
        key: 'platform-tenants', label: 'Tenants', icon: Building, allowedRoles: ['Super Admin'],
        children: [
          { key: 'all-companies', label: 'All Companies', path: '/tenants/companies', allowedRoles: ['Super Admin'] },
          { key: 'subscriptions', label: 'Subscriptions', path: '/tenants/subscriptions', allowedRoles: ['Super Admin'] },
          { key: 'tenant-addons', label: 'Add-ons', path: '/tenants/addons', allowedRoles: ['Super Admin'] },
          { key: 'provisioning', label: 'Tenant Provisioning', path: '/tenants/provisioning', allowedRoles: ['Super Admin'] },
        ]
      },
      {
        key: 'global-settings', label: 'Global Settings', icon: Globe, allowedRoles: ['Super Admin'],
        children: [
          { key: 'platform-config', label: 'Platform Config', path: '/settings/global', allowedRoles: ['Super Admin'] },
          { key: 'feature-flags', label: 'Feature Flags', path: '/settings/flags', allowedRoles: ['Super Admin'] },
        ]
      },
      { key: 'global-logs', label: 'Platform Audit Logs', path: '/audit/platform', icon: FileKey, allowedRoles: ['Super Admin'] },
      { key: 'system-audit-dash', label: 'System Audit Dashboard', path: '/dashboards/system-audit', icon: Activity, allowedRoles: ['Super Admin'] },
      { key: 'system-logs', label: 'System Log Explorer', path: '/audit/system-logs', icon: FileText, allowedRoles: ['Super Admin', 'IT Admin'] },
      { key: 'cold-email', label: 'Cold Email Campaigns', path: '/marketing/cold-campaigns', icon: Mail, allowedRoles: ['Super Admin'] },
    ]
  },
  {
    section: 'Company Admin Operations',
    items: [
      {
        key: 'organization', label: 'Organization', icon: Building, allowedRoles: ['Company Admin'],
        children: [
          { key: 'org-profile', label: 'Company Profile', path: '/organization/profile', allowedRoles: ['Company Admin'] },
          { key: 'org-legal', label: 'Legal Entities', path: '/organization/legal-entities', allowedRoles: ['Company Admin'] },
          { key: 'org-branches', label: 'Branches', path: '/organization/branches', allowedRoles: ['Company Admin'] },
          { key: 'org-employee-types', label: 'Employee Types', path: '/organization/employee-types', allowedRoles: ['Company Admin', 'HR Admin'] },
          { key: 'org-departments', label: 'Departments', path: '/organization/departments', allowedRoles: ['Company Admin'] },
          { key: 'org-designations', label: 'Designations', path: '/organization/designations', allowedRoles: ['Company Admin'] },
        ]
      },
      {
        key: 'admin-config', label: 'Admin Configuration', icon: Settings, allowedRoles: ['Company Admin'],
        children: [
          { key: 'roles-perms', label: 'Roles & Permissions', path: '/iam/roles', allowedRoles: ['Company Admin'] },
          { key: 'workflow-designer', label: 'Workflow Designer', path: '/settings/workflows', allowedRoles: ['Company Admin'] },
          { key: 'tenant-email', label: 'Email Settings', path: '/settings/email', allowedRoles: ['Company Admin', 'HR Admin'] },
        ]
      },
      {
        key: 'company-policies', label: 'Company Policies', icon: FileText, allowedRoles: ['Company Admin'],
        children: [
          { key: 'holiday-calendar', label: 'Holiday Calendar', path: '/policies/holidays', allowedRoles: ['Company Admin', 'HR Admin'] },
          { key: 'general-policies', label: 'General Policies', path: '/policies/general', allowedRoles: ['Company Admin'] },
        ]
      },
    ]
  },
  {
    section: 'HR Operations',
    items: [
      {
        key: 'employees', label: 'Employees', icon: Users, allowedRoles: ['Company Admin', 'HR Admin'],
        children: [
          { key: 'emp-directory', label: 'Directory', path: '/employees/directory', allowedRoles: ['Company Admin', 'HR Admin'] },
          { key: 'emp-add', label: 'Add Employee', path: '/employees/add', allowedRoles: ['HR Admin'] },
          { key: 'emp-orgchart', label: 'Org Chart', path: '/employees/org-chart', allowedRoles: ['Super Admin', 'Company Admin', 'HR Admin', 'Employee'] },
        ]
      },
      {
        key: 'onboarding', label: 'Onboarding', icon: ClipboardList, allowedRoles: ['HR Admin'],
        children: [
          { key: 'onb-checklists', label: 'Checklists', path: '/onboarding/checklists', allowedRoles: ['HR Admin'] },
          { key: 'onb-bgv', label: 'BGV Status', path: '/onboarding/bgv', allowedRoles: ['HR Admin'] },
        ]
      },
      {
        key: 'attendance', label: 'Attendance & Shifts', icon: Clock, allowedRoles: ['HR Admin'],
        children: [
          { key: 'att-live', label: 'Live Tracking', path: '/attendance/live', allowedRoles: ['HR Admin'] },
          { key: 'att-field', label: 'Field Tracking Map', path: '/attendance/field-tracking', allowedRoles: ['HR Admin', 'Company Admin', 'Super Admin'] },
          { key: 'att-rosters', label: 'Rosters', path: '/attendance/rosters', allowedRoles: ['HR Admin'] },
          { key: 'att-reg', label: 'Regularization Queue', path: '/attendance/regularization', allowedRoles: ['HR Admin'] },
        ]
      },
      {
        key: 'wfh-hr', label: 'WFH Tracking', icon: MonitorCheck, allowedRoles: ['HR Admin'],
        children: [
          { key: 'hr-wfh-requests', label: 'WFH Requests', path: '/hr/wfh-requests', allowedRoles: ['HR Admin'] },
          { key: 'hr-wfh-policy', label: 'WFH Policy', path: '/hr/wfh-policy', allowedRoles: ['HR Admin'] },
          { key: 'hr-wfh-sessions', label: 'WFH Sessions', path: '/hr/wfh-sessions', allowedRoles: ['HR Admin'] },
          { key: 'hr-wfh-reports', label: 'WFH Reports', path: '/hr/wfh-reports', allowedRoles: ['HR Admin'] },
        ]
      },
      { key: 'email-logs', label: 'Email Logs', path: '/hr/email-logs', icon: Mail, allowedRoles: ['Company Admin', 'HR Admin'] },
      {
        key: 'leave-management', label: 'Leave Management', icon: Calendar, allowedRoles: ['HR Admin'],
        children: [
          { key: 'lm-policies', label: 'Leave Policies', path: '/leave/policies', allowedRoles: ['HR Admin'] },
          { key: 'lm-balance', label: 'Balance Adjustments', path: '/leave/balances', allowedRoles: ['HR Admin'] },
          { key: 'lm-team', label: 'Team Calendar', path: '/leave/team', allowedRoles: ['HR Admin'] },
        ]
      },
      {
        key: 'offboarding', label: 'Offboarding', icon: LogOut, allowedRoles: ['HR Admin'],
        children: [
          { key: 'off-resignation', label: 'Resignation Queue', path: '/offboarding/resignations', allowedRoles: ['HR Admin'] },
          { key: 'off-clearance', label: 'Clearance Tracker', path: '/offboarding/clearance', allowedRoles: ['HR Admin'] },
        ]
      },
      {
        key: 'hr-documents', label: 'Documents', icon: FilePlus, allowedRoles: ['HR Admin'],
        children: [
          { key: 'doc-templates', label: 'Letter Templates', path: '/documents/templates', allowedRoles: ['HR Admin'] },
          { key: 'doc-vault', label: 'Document Vault', path: '/documents/vault', allowedRoles: ['HR Admin'] },
        ]
      },
      {
        key: 'engagement', label: 'Engagement', icon: Target, allowedRoles: ['HR Admin'],
        children: [
          { key: 'eng-announcements', label: 'Announcements', path: '/engagement/announcements', allowedRoles: ['HR Admin'] },
          { key: 'eng-surveys', label: 'Surveys', path: '/engagement/surveys', allowedRoles: ['HR Admin'] },
        ]
      },
    ]
  },
  {
    section: 'Payroll & Finance',
    items: [
      {
        key: 'payroll-config', label: 'Payroll Config', icon: Settings, allowedRoles: ['Payroll Admin'],
        children: [
          { key: 'pc-settings', label: 'Payroll Settings', path: '/payroll/settings', allowedRoles: ['Payroll Admin', 'Company Admin'] },
          { key: 'pc-structures', label: 'Salary Structures', path: '/payroll/structures', allowedRoles: ['Payroll Admin', 'Company Admin'] },
          { key: 'pc-components', label: 'Salary Components', path: '/payroll/components', allowedRoles: ['Payroll Admin'] },
          { key: 'pc-tax', label: 'Tax Declarations', path: '/payroll/tax-regimes', allowedRoles: ['Payroll Admin'] },
        ]
      },
      {
        key: 'payroll-runs', label: 'Payroll Runs', icon: HandCoins, allowedRoles: ['Payroll Admin'],
        children: [
          { key: 'pr-generate', label: 'Generate', path: '/payroll/generate', allowedRoles: ['Payroll Admin'] },
          { key: 'pr-review', label: 'Review', path: '/payroll/review', allowedRoles: ['Payroll Admin'] },
          { key: 'pr-lock', label: 'Lock & Release', path: '/payroll/lock', allowedRoles: ['Payroll Admin'] },
        ]
      },
      {
        key: 'payroll-compliance', label: 'Statutory Compliance', icon: ShieldCheck, allowedRoles: ['Payroll Admin'],
        children: [
          { key: 'comp-in', label: 'India (PF/ESIC/Form 16)', path: '/payroll/compliance', allowedRoles: ['Payroll Admin'], jurisdictions: ['IN'] },
          { key: 'comp-us', label: 'USA (W-2/941)', path: '/payroll/compliance-us', allowedRoles: ['Payroll Admin'], jurisdictions: ['US'] },
          { key: 'comp-ca', label: 'Canada (T4)', path: '/payroll/compliance-ca', allowedRoles: ['Payroll Admin'], jurisdictions: ['CA'] },
        ]
      },
      {
        key: 'payroll-dist', label: 'Distributions', icon: BadgeIndianRupee, allowedRoles: ['Payroll Admin'],
        children: [
          { key: 'dist-payslips', label: 'Payslip Release', path: '/payroll/payslips', allowedRoles: ['Payroll Admin'] },
          { key: 'dist-bank', label: 'Bank Transfer CSVs', path: '/payroll/bank', allowedRoles: ['Payroll Admin'] },
        ]
      },
      {
        key: 'finance-expenses', label: 'Expenses', icon: Receipt, allowedRoles: ['Finance Admin'],
        children: [
          { key: 'exp-pending', label: 'Pending Claims', path: '/expenses/pending', allowedRoles: ['Finance Admin'] },
          { key: 'exp-policies', label: 'Expense Policies', path: '/expenses/policies', allowedRoles: ['Finance Admin'] },
          { key: 'exp-categories', label: 'Category Master', path: '/expenses/categories', allowedRoles: ['Finance Admin'] },
        ]
      },
      {
        key: 'finance-settlements', label: 'Settlements', icon: CheckSquare, allowedRoles: ['Finance Admin'],
        children: [
          { key: 'set-fnf', label: 'Full & Final (F&F)', path: '/finance/fnf', allowedRoles: ['Finance Admin'] },
        ]
      },
      {
        key: 'finance-billing', label: 'Billing (PSA)', icon: FileText, allowedRoles: ['Finance Admin'],
        children: [
          { key: 'bill-invoices', label: 'Client Invoices', path: '/finance/invoices', allowedRoles: ['Finance Admin'] },
          { key: 'bill-timesheets', label: 'Timesheet Profitability', path: '/finance/timesheets', allowedRoles: ['Finance Admin'] },
        ]
      },
    ]
  },
  {
    section: 'IT & Audit',
    items: [
      {
        key: 'it-system', label: 'System Access', icon: ShieldCheck, allowedRoles: ['IT Admin'],
        children: [
          { key: 'sys-creds', label: 'User Credentials', path: '/it/credentials', allowedRoles: ['IT Admin'] },
          { key: 'sys-mfa', label: 'MFA Settings', path: '/it/mfa', allowedRoles: ['IT Admin'] },
          { key: 'sys-sso', label: 'SSO Integration', path: '/it/sso', allowedRoles: ['IT Admin'] },
        ]
      },
      {
        key: 'it-assets', label: 'Asset Management', icon: MonitorCheck, allowedRoles: ['IT Admin'],
        children: [
          { key: 'asset-list', label: 'Inventory List', path: '/assets/list', allowedRoles: ['IT Admin'] },
          { key: 'asset-assign', label: 'Assignments', path: '/assets/assignments', allowedRoles: ['IT Admin'] },
          { key: 'asset-warranty', label: 'Warranties', path: '/assets/warranties', allowedRoles: ['IT Admin'] },
        ]
      },
      {
        key: 'it-integrations', label: 'Integrations', icon: Fingerprint, allowedRoles: ['IT Admin'],
        children: [
          { key: 'int-bio', label: 'Biometric Device Sync', path: '/it/biometrics', allowedRoles: ['IT Admin'] },
          { key: 'int-webhooks', label: 'Webhooks & API', path: '/it/api', allowedRoles: ['IT Admin'] },
        ]
      },
      {
        key: 'it-tracker', label: 'WFH Tracker Admin', icon: MonitorCheck, allowedRoles: ['IT Admin', 'Company Admin'],
        children: [
          { key: 'adm-tracker-settings', label: 'Tracker Settings', path: '/admin/tracker-settings', allowedRoles: ['IT Admin', 'Company Admin'] },
          { key: 'adm-tracker-devices', label: 'Tracker Devices', path: '/admin/tracker-devices', allowedRoles: ['IT Admin', 'Company Admin'] },
          { key: 'adm-screenshot-ret', label: 'Screenshot Retention', path: '/admin/screenshot-retention', allowedRoles: ['IT Admin', 'Company Admin'] },
          { key: 'adm-audit-logs', label: 'Tracker Audit Logs', path: '/admin/audit-logs', allowedRoles: ['IT Admin', 'Company Admin'] },
        ]
      },
      {
        key: 'audit-logs', label: 'System Logs', icon: FileKey, allowedRoles: ['Auditor'],
        children: [
          { key: 'log-admin', label: 'Admin Action Audits', path: '/audit/admin', allowedRoles: ['Auditor'] },
          { key: 'log-login', label: 'Login Logs', path: '/audit/logins', allowedRoles: ['Auditor'] },
        ]
      },
      {
        key: 'audit-reports', label: 'Compliance Reports', icon: PieChart, allowedRoles: ['Auditor'],
        children: [
          { key: 'rep-hist', label: 'Historical Payroll', path: '/audit/payroll', allowedRoles: ['Auditor'] },
          { key: 'rep-tax', label: 'Tax Filings', path: '/audit/tax', allowedRoles: ['Auditor'] },
          { key: 'rep-att', label: 'Attendance Summaries', path: '/audit/attendance', allowedRoles: ['Auditor'] },
        ]
      },
    ]
  },
  {
    section: 'Manager & ATS',
    items: [
      {
        key: 'mgr-approvals', label: 'Approvals Inbox', icon: CheckSquare, allowedRoles: ['Manager'],
        children: [
          { key: 'app-leaves', label: 'Leaves', path: '/manager/approvals/leaves', allowedRoles: ['Manager'] },
          { key: 'app-att', label: 'Attendance', path: '/manager/approvals/attendance', allowedRoles: ['Manager'] },
          { key: 'app-exp', label: 'Expenses', path: '/manager/approvals/expenses', allowedRoles: ['Manager'] },
          { key: 'app-ot', label: 'Overtime', path: '/manager/approvals/overtime', allowedRoles: ['Manager'] },
        ]
      },
      {
        key: 'mgr-team', label: 'My Team', icon: UsersRound, allowedRoles: ['Manager'],
        children: [
          { key: 'team-att', label: 'Team Attendance', path: '/manager/team/attendance', allowedRoles: ['Manager'] },
          { key: 'team-leaves', label: 'Leave Calendar', path: '/manager/team/leaves', allowedRoles: ['Manager'] },
          { key: 'team-profiles', label: 'Subordinate Profiles', path: '/manager/team/profiles', allowedRoles: ['Manager'] },
        ]
      },
      {
        key: 'mgr-wfh', label: 'WFH Tracking', icon: MonitorCheck, allowedRoles: ['Manager'],
        children: [
          { key: 'mgr-wfh-approvals', label: 'WFH Approvals', path: '/manager/wfh-approvals', allowedRoles: ['Manager'] },
          { key: 'mgr-team-wfh', label: 'Team WFH Sessions', path: '/manager/team-wfh-sessions', allowedRoles: ['Manager'] },
          { key: 'mgr-team-prod', label: 'Team Productivity', path: '/manager/team-productivity', allowedRoles: ['Manager'] },
        ]
      },
      {
        key: 'mgr-perf', label: 'Performance', icon: Target, allowedRoles: ['Manager'],
        children: [
          { key: 'perf-goals', label: 'Team Goals', path: '/manager/performance/goals', allowedRoles: ['Manager'] },
          { key: 'perf-reviews', label: 'Review Appraisals', path: '/manager/performance/reviews', allowedRoles: ['Manager'] },
        ]
      },
      {
        key: 'mgr-rec', label: 'Recruitment', icon: Briefcase, allowedRoles: ['Manager'],
        children: [
          { key: 'rec-myreqs', label: 'My Requisitions', path: '/manager/recruitment/requisitions', allowedRoles: ['Manager'] },
          { key: 'rec-feedback', label: 'Interview Feedback', path: '/manager/recruitment/feedback', allowedRoles: ['Manager'] },
        ]
      },
      {
        key: 'ats-jobs', label: 'Job Management', icon: Briefcase, allowedRoles: ['Recruiter'],
        children: [
          { key: 'job-reqs', label: 'Requisitions', path: '/recruitment/requisitions', allowedRoles: ['Recruiter'] },
          { key: 'job-active', label: 'Active Postings', path: '/recruitment/active', allowedRoles: ['Recruiter'] },
          { key: 'job-career', label: 'Career Board', path: '/recruitment/career-portal', allowedRoles: ['Recruiter', 'HR Admin'] },
        ]
      },
      {
        key: 'ats-pipeline', label: 'Candidate Pipeline', icon: Users, allowedRoles: ['Recruiter'],
        children: [
          { key: 'pipe-kanban', label: 'Kanban Board', path: '/recruitment/pipeline', allowedRoles: ['Recruiter'] },
          { key: 'pipe-ai', label: 'AI Match Scores', path: '/recruitment/ai-scores', allowedRoles: ['Recruiter'] },
          { key: 'pipe-cand-new', label: 'Add Candidate (AI)', path: '/recruitment/candidates/new', allowedRoles: ['Recruiter', 'HR Admin', 'Company Admin'] },
        ]
      },
      {
        key: 'ats-interviews', label: 'Interviews', icon: Calendar, allowedRoles: ['Recruiter', 'Interviewer', 'HR Admin', 'Company Admin'],
        children: [
          { key: 'int-sched', label: 'Scheduling', path: '/recruitment/interviews', allowedRoles: ['Recruiter', 'Interviewer', 'HR Admin', 'Company Admin'] },
          { key: 'int-aireports', label: 'AI Interview Reports', path: '/recruitment/ai-interviews', allowedRoles: ['Recruiter', 'Interviewer'] },
          { key: 'int-assessments', label: 'Assessment Builder', path: '/recruitment/assessments', allowedRoles: ['Recruiter'] },
          { key: 'int-my', label: 'My Interviews', path: '/interviewer/upcoming', allowedRoles: ['Interviewer'] },
          { key: 'int-feedback', label: 'Submit Feedback', path: '/interviewer/feedback', allowedRoles: ['Interviewer'] },
        ]
      },
      {
        key: 'ats-offers', label: 'Offers', icon: FileText, allowedRoles: ['Recruiter'],
        children: [
          { key: 'offer-gen', label: 'Offer Generation', path: '/recruitment/offers', allowedRoles: ['Recruiter'] },
          { key: 'offer-track', label: 'Candidate Portal Tracking', path: '/recruitment/offer-tracking', allowedRoles: ['Recruiter'] },
        ]
      },
    ]
  },
  {
    section: 'Self Service',
    items: [
      {
        key: 'ess-attendance', label: 'Attendance', icon: Clock, allowedRoles: ['Employee'],
        children: [
          { key: 'att-web', label: 'Web Check-in/out', path: '/ess/attendance/web', allowedRoles: ['Employee'] },
          { key: 'att-logs', label: 'My Logs', path: '/ess/attendance/logs', allowedRoles: ['Employee'] },
          { key: 'att-reg', label: 'Regularization Request', path: '/ess/attendance/regularize', allowedRoles: ['Employee'] },
        ]
      },
      {
        key: 'ess-wfh', label: 'Work From Home', icon: MonitorCheck, allowedRoles: ['Employee'],
        children: [
          { key: 'wfh-request', label: 'Request WFH', path: '/wfh/request', allowedRoles: ['Employee'] },
          { key: 'wfh-my-requests', label: 'My WFH Requests', path: '/wfh/my-requests', allowedRoles: ['Employee'] },
          { key: 'wfh-tracker-status', label: 'Tracker Status', path: '/wfh/tracker-status', allowedRoles: ['Employee'] },
          { key: 'wfh-my-sessions', label: 'My Sessions', path: '/wfh/my-sessions', allowedRoles: ['Employee'] },
        ]
      },
      {
        key: 'ess-leaves', label: 'Leaves', icon: Calendar, allowedRoles: ['Employee'],
        children: [
          { key: 'leave-apply', label: 'Apply Leave', path: '/ess/leaves/apply', allowedRoles: ['Employee'] },
          { key: 'leave-bal', label: 'My Balances', path: '/ess/leaves/balances', allowedRoles: ['Employee'] },
          { key: 'leave-hol', label: 'Holiday List', path: '/ess/leaves/holidays', allowedRoles: ['Employee'] },
        ]
      },
      {
        key: 'ess-finance', label: 'Finance', icon: BadgeIndianRupee, allowedRoles: ['Employee'],
        children: [
          { key: 'fin-payslips', label: 'My Payslips', path: '/ess/finance/payslips', allowedRoles: ['Employee'] },
          { key: 'fin-tax', label: 'Tax Declarations', path: '/ess/finance/tax', allowedRoles: ['Employee'] },
          { key: 'fin-exp', label: 'Expense Claims', path: '/ess/finance/expenses', allowedRoles: ['Employee'] },
        ]
      },
      {
        key: 'ess-helpdesk', label: 'Helpdesk', icon: Stethoscope, allowedRoles: ['Employee'],
        children: [
          { key: 'hd-raise', label: 'Raise IT/HR Ticket', path: '/ess/helpdesk/raise', allowedRoles: ['Employee'] },
          { key: 'hd-my', label: 'My Tickets', path: '/ess/helpdesk/my-tickets', allowedRoles: ['Employee'] },
        ]
      },
      {
        key: 'ess-perf', label: 'Performance', icon: Target, allowedRoles: ['Employee'],
        children: [
          { key: 'perf-goals', label: 'My Goals', path: '/ess/performance/goals', allowedRoles: ['Employee'] },
        ]
      },
      {
        key: 'ess-orgchart', label: 'Organization', icon: Users, allowedRoles: ['Employee'],
        path: '/employees/org-chart',
      },
    ]
  }
];
