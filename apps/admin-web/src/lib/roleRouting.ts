import type { Role } from '@/config/menuConfig';

const ROLE_HOME: Record<Role, string> = {
  'Super Admin': '/dashboards/platform',
  'Company Admin': '/dashboards/company',
  'HR Admin': '/dashboards/hr',
  'Payroll Admin': '/dashboards/payroll',
  'Finance Admin': '/dashboards/finance',
  'IT Admin': '/dashboards/it',
  Manager: '/dashboards/manager',
  Recruiter: '/dashboards/recruitment',
  Interviewer: '/interviewer/upcoming',
  Auditor: '/dashboards/audit',
  Employee: '/dashboards/employee',
};

/** Highest-privilege role wins when a user has multiple mappings. */
const ROLE_PRIORITY: Role[] = [
  'Super Admin',
  'Company Admin',
  'HR Admin',
  'Payroll Admin',
  'Finance Admin',
  'IT Admin',
  'Manager',
  'Recruiter',
  'Auditor',
  'Interviewer',
  'Employee',
];

export function getRoleHomeRoute(role: Role | string): string {
  return ROLE_HOME[role as Role] ?? '/dashboards/employee';
}

export function getPrimaryRole(roles: string[]): Role {
  for (const preferred of ROLE_PRIORITY) {
    if (roles.includes(preferred)) return preferred;
  }
  return (roles[0] as Role) || 'Employee';
}

const VALID_ROLES = new Set<Role>(ROLE_PRIORITY);

export function parseUserRoles(roles: string[]): Role[] {
  const out = new Set<Role>();
  for (const r of roles) {
    if (VALID_ROLES.has(r as Role)) out.add(r as Role);
  }
  if (out.size === 0) out.add('Employee');
  return Array.from(out);
}

export type AuthMeUser = {
  email: string;
  display_name?: string;
  roles: string[];
};

export function resolvePostLoginRoute(user: AuthMeUser): string {
  const primary = getPrimaryRole(user.roles);
  return getRoleHomeRoute(primary);
}

export function isDashboardPath(pathname: string): boolean {
  return pathname.startsWith('/dashboards/');
}
