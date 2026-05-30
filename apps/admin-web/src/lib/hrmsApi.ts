import api from './axios';

export const employeesApi = {
  list: (params?: Record<string, string | number>) => api.get('/employees/employees/', { params }),
  get: (id: string) => api.get(`/employees/employees/${id}/`),
  create: (data: Record<string, unknown>) => api.post('/employees/employees/', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/employees/employees/${id}/`, data),
  delete: (id: string) => api.delete(`/employees/employees/${id}/`),
  orgTree: () => api.get('/employees/employees/org-tree/'),
  search: (q: string) => api.get('/employees/employees/', { params: { search: q, page_size: 8 } }),
  employeeTypes: {
    list: () => api.get('/employees/employee-types/'),
    create: (data: Record<string, unknown>) => api.post('/employees/employee-types/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/employees/employee-types/${id}/`, data),
    delete: (id: string) => api.delete(`/employees/employee-types/${id}/`),
  },
  documents: {
    list: (params?: Record<string, string>) => api.get('/employees/documents/', { params }),
    upload: (formData: FormData) =>
      api.post('/employees/documents/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    delete: (id: string) => api.delete(`/employees/documents/${id}/`),
  },
  contacts: {
    list: () => api.get('/employees/contacts/'),
    create: (data: Record<string, unknown>) => api.post('/employees/contacts/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/employees/contacts/${id}/`, data),
  },
  banks: {
    list: () => api.get('/employees/banks/'),
    create: (data: Record<string, unknown>) => api.post('/employees/banks/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/employees/banks/${id}/`, data),
  },
  taxes: {
    list: () => api.get('/employees/taxes/'),
    create: (data: Record<string, unknown>) => api.post('/employees/taxes/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/employees/taxes/${id}/`, data),
  },
  me: {
    get: () => api.get('/employees/me/'),
    update: (data: Record<string, unknown>) => api.patch('/employees/me/', data),
    bank: () => api.get('/employees/me/bank/'),
    assets: () => api.get('/employees/me/assets/'),
    workLocation: () => api.get('/employees/me/work-location/'),
    updateWorkLocation: (data: Record<string, unknown>) => api.patch('/employees/me/work-location/', data),
  },
};

export const organizationApi = {
  companyProfiles: {
    list: () => api.get('/company-profiles/'),
    create: (data: Record<string, unknown>) => api.post('/company-profiles/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/company-profiles/${id}/`, data),
    delete: (id: string) => api.delete(`/company-profiles/${id}/`),
  },
  branches: {
    list: () => api.get('/branches/'),
    create: (data: Record<string, unknown>) => api.post('/branches/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/branches/${id}/`, data),
    delete: (id: string) => api.delete(`/branches/${id}/`),
  },
  departments: {
    list: () => api.get('/departments/'),
    create: (data: Record<string, unknown>) => api.post('/departments/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/departments/${id}/`, data),
    delete: (id: string) => api.delete(`/departments/${id}/`),
  },
  designations: {
    list: () => api.get('/designations/'),
    create: (data: Record<string, unknown>) => api.post('/designations/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/designations/${id}/`, data),
    delete: (id: string) => api.delete(`/designations/${id}/`),
  },
  holidays: {
    list: () => api.get('/holidays/'),
    create: (data: Record<string, unknown>) => api.post('/holidays/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/holidays/${id}/`, data),
    delete: (id: string) => api.delete(`/holidays/${id}/`),
  },
};

export const notificationsApi = {
  list: () => api.get('/notifications/notifications/'),
  markRead: (id: string) => api.patch(`/notifications/notifications/${id}/`, { is_read: true }),
  markAllRead: () => api.post('/notifications/notifications/mark_all_read/'),
  unreadCount: () => api.get('/notifications/notifications/unread_count/'),
};

export const tenantEmailApi = {
  get: () => api.get('/tenant-email-settings/'),
  update: (data: Record<string, unknown>) => api.patch('/tenant-email-settings/', data),
  testSend: (to_email?: string) =>
    api.post('/tenant-email-settings/test-send/', to_email ? { to_email } : {}),
};

export const outboundEmailApi = {
  list: (params?: Record<string, string>) => api.get('/outbound-email-logs/', { params }),
  resend: (id: string) => api.post(`/outbound-email-logs/${id}/resend/`),
  notify: (id: string) => api.post(`/outbound-email-logs/${id}/notify/`),
};

export const platformHealthApi = {
  modules: () => api.get('/platform/health/modules/'),
  testSmtp: (to_email: string) => api.post('/env-configs/SMTP/test/', { to_email }),
  testImap: () => api.post('/env-configs/IMAP/test/'),
  simulateImapPoll: () => api.post('/email/simulate/', { action: 'imap_poll' }),
};

export const attendanceApi = {
  logs: {
    list: (params?: Record<string, string>) => api.get('/attendance/logs/', { params }),
    punchIn: (formData: FormData) =>
      api.post('/attendance/logs/punch_in/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    punchOut: (formData: FormData) =>
      api.post('/attendance/logs/punch_out/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  },
  fieldPings: {
    create: (data: Record<string, unknown>) => api.post('/attendance/field-pings/', data),
    live: () => api.get('/attendance/field-pings/live/'),
    trail: (params: Record<string, string>) => api.get('/attendance/field-pings/trail/', { params }),
  },
  regularizations: {
    list: () => api.get('/attendance/regularizations/'),
    create: (data: Record<string, unknown>) => api.post('/attendance/regularizations/', data),
    approve: (id: string) => api.post(`/attendance/regularizations/${id}/approve/`),
    reject: (id: string, reason?: string) =>
      api.post(`/attendance/regularizations/${id}/reject/`, { reason }),
  },
  geofences: {
    list: () => api.get('/attendance/geofences/'),
    create: (data: Record<string, unknown>) => api.post('/attendance/geofences/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/attendance/geofences/${id}/`, data),
    delete: (id: string) => api.delete(`/attendance/geofences/${id}/`),
  },
  settings: {
    get: () => api.get('/attendance/settings/'),
    update: (data: Record<string, unknown>) => api.put('/attendance/settings/', data),
  },
};

export const leaveApi = {
  types: { list: () => api.get('/leave/types/') },
  policies: {
    list: () => api.get('/leave/policies/'),
    create: (data: Record<string, unknown>) => api.post('/leave/policies/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/leave/policies/${id}/`, data),
  },
  balances: {
    list: () => api.get('/leave/balances/'),
    update: (id: string, data: Record<string, unknown>) => api.patch(`/leave/balances/${id}/`, data),
  },
  requests: {
    list: () => api.get('/leave/requests/'),
    apply: (data: Record<string, unknown>) => api.post('/leave/requests/apply_leave/', data),
    approve: (id: string) => api.post(`/leave/requests/${id}/approve/`),
    reject: (id: string, reason?: string) => api.post(`/leave/requests/${id}/reject/`, { reason }),
  },
};

export const payrollApi = {
  components: {
    list: () => api.get('/payroll/components/'),
    create: (data: Record<string, unknown>) => api.post('/payroll/components/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/payroll/components/${id}/`, data),
    delete: (id: string) => api.delete(`/payroll/components/${id}/`),
  },
  runs: {
    list: () => api.get('/payroll/runs/'),
    create: (data: Record<string, unknown>) => api.post('/payroll/runs/', data),
    generate: (id: string) => api.post(`/payroll/runs/${id}/generate/`),
    approve: (id: string) => api.post(`/payroll/runs/${id}/approve/`),
    lock: (id: string) => api.post(`/payroll/runs/${id}/lock/`),
    release: (id: string) => api.post(`/payroll/runs/${id}/release/`),
    bankExport: (id: string) => api.get(`/payroll/runs/${id}/bank_export/`, { responseType: 'blob' }),
  },
  payslips: {
    list: () => api.get('/payroll/payslips/'),
    pdf: (id: string) => api.get(`/payroll/payslips/${id}/pdf/`, { responseType: 'blob' }),
  },
  declarations: {
    list: (params?: Record<string, string>) => api.get('/payroll/declarations/', { params }),
    create: (data: Record<string, unknown>) => api.post('/payroll/declarations/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/payroll/declarations/${id}/`, data),
  },
  taxTips: {
    credits: () => api.get('/payroll/tax-tips/credits/'),
    generate: (data: { jurisdiction: string; fiscal_year: number }) =>
      api.post('/payroll/tax-tips/generate/', data),
  },
  structures: {
    list: () => api.get('/payroll/structures/'),
    update: (id: string, data: Record<string, unknown>) => api.patch(`/payroll/structures/${id}/`, data),
  },
  settings: {
    get: () => api.get('/payroll/settings/'),
    patch: (data: Record<string, unknown>) => api.patch('/payroll/settings/', data),
  },
};

export const complianceApi = {
  documents: { list: () => api.get('/compliance/documents/') },
  form16: (fy: number) => api.post('/compliance/actions/form16/generate/', { fy }),
  form12ba: (fy: number) => api.post('/compliance/actions/form12ba/generate/', { fy }),
  w2: (taxYear: number) => api.post('/compliance/actions/w2/generate/', { tax_year: taxYear }),
  form1095c: (taxYear: number) => api.post('/compliance/actions/1095c/generate/', { tax_year: taxYear }),
  t4: (taxYear: number) => api.post('/compliance/actions/t4/generate/', { tax_year: taxYear }),
  rl1: (taxYear: number) => api.post('/compliance/actions/rl1/generate/', { tax_year: taxYear }),
  bulkYearEnd: (fy: number) => api.post('/compliance/actions/bulk-year-end/', { fy }),
  itrAssist: (fy: number, employeeId: string) => api.post('/compliance/actions/itr-assist/', { fy, employee_id: employeeId }),
};

export const legalEntitiesApi = {
  list: () => api.get('/legal-entities/'),
  create: (data: Record<string, unknown>) => api.post('/legal-entities/', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/legal-entities/${id}/`, data),
};

export const platformAddonsApi = {
  list: (params?: Record<string, string>) => api.get('/platform/tenant-addons/', { params }),
  upsert: (data: { tenant: string; addon_code: string; enabled: boolean; notes?: string }) =>
    api.post('/platform/tenant-addons/upsert/', data),
};

export const recruitmentApi = {
  jobs: {
    list: (params?: Record<string, string>) => api.get('/recruitment/jobs/', { params }),
    create: (data: Record<string, unknown>) => api.post('/recruitment/jobs/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/recruitment/jobs/${id}/`, data),
    get: (id: string) => api.get(`/recruitment/jobs/${id}/`),
    publish: (id: string) => api.post(`/recruitment/jobs/${id}/publish/`),
    unpublish: (id: string) => api.post(`/recruitment/jobs/${id}/unpublish/`),
  },
  careerPortal: {
    settings: () => api.get('/recruitment/career-portal/settings/'),
    updateSettings: (data: Record<string, unknown>) =>
      api.patch('/recruitment/career-portal/settings/update_settings/', data),
    regenerateKey: () => api.post('/recruitment/career-portal/settings/regenerate-key/'),
    embedSnippet: () => api.get('/recruitment/career-portal/settings/embed-snippet/'),
  },
  campaigns: {
    list: () => api.get('/recruitment/campaigns/'),
    get: (id: string) => api.get(`/recruitment/campaigns/${id}/`),
    create: (formData: FormData) =>
      api.post('/recruitment/campaigns/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    launch: (id: string) => api.post(`/recruitment/campaigns/${id}/launch/`),
    generateCopy: (id: string) => api.post(`/recruitment/campaigns/${id}/generate-copy/`),
  },
  candidates: {
    list: (params?: Record<string, string>) => api.get('/recruitment/candidates/', { params }),
    create: (formData: FormData) =>
      api.post('/recruitment/candidates/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    match: (id: string) => api.post(`/recruitment/candidates/${id}/match/`),
    invite: (
      id: string,
      data?: {
        send_email?: boolean;
        expiry_minutes?: number;
        scheduled_at?: string;
        cc_hr_admin?: boolean;
        cc_emails?: string[];
        force?: boolean;
        include_assessment?: boolean;
      },
    ) => api.post(`/recruitment/candidates/${id}/invite/`, data ?? {}),
  },
  interviews: { list: () => api.get('/recruitment/interviews/') },
  aiSessions: {
    list: () => api.get('/recruitment/ai-sessions/'),
    getLive: (id: string) => api.get(`/recruitment/ai-sessions/${id}/live/`),
    terminate: (id: string) => api.post(`/recruitment/ai-sessions/${id}/terminate/`),
    flagConcern: (id: string, note?: string) =>
      api.post(`/recruitment/ai-sessions/${id}/flag-concern/`, { note }),
  },
  settings: {
    get: () => api.get('/recruitment/settings/'),
    update: (data: Record<string, unknown>) =>
      api.patch('/recruitment/settings/update_settings/', data),
  },
  aiReports: {
    list: () => api.get('/recruitment/ai-reports/'),
    get: (id: string) => api.get(`/recruitment/ai-reports/${id}/`),
  },
  assessmentTemplates: {
    list: () => api.get('/recruitment/assessment-templates/'),
    create: (data: Record<string, unknown>) => api.post('/recruitment/assessment-templates/', data),
    generate: (id: string) => api.post(`/recruitment/assessment-templates/${id}/generate/`),
  },
};

export const tenantsApi = {
  list: () => api.get('/tenants/'),
  create: (data: Record<string, unknown>) => api.post('/tenants/', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/tenants/${id}/`, data),
};

export const dashboardsApi = {
  hr: () => api.get('/dashboards/hr/'),
  manager: () => api.get('/dashboards/manager/'),
  company: () => api.get('/dashboards/company/'),
  employee: () => api.get('/dashboards/employee/'),
  payroll: () => api.get('/dashboards/payroll/'),
  finance: () => api.get('/dashboards/finance/'),
  it: () => api.get('/dashboards/it/'),
  recruitment: () => api.get('/dashboards/recruitment/'),
  audit: () => api.get('/dashboards/audit/'),
  platform: () => api.get('/platform/monitoring/'),
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export function unwrapList<T>(data: PaginatedResponse<T> | T[]): T[] {
  if (Array.isArray(data)) return data;
  return data.results ?? [];
}
