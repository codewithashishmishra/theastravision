import api from './axios';

export const employeesApi = {
  list: (params?: Record<string, string | number>) => api.get('/employees/employees/', { params }),
  get: (id: string) => api.get(`/employees/employees/${id}/`),
  create: (data: Record<string, unknown>) => api.post('/employees/employees/', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/employees/employees/${id}/`, data),
  delete: (id: string) => api.delete(`/employees/employees/${id}/`),
  search: (q: string) => api.get('/employees/employees/', { params: { search: q, page_size: 8 } }),
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

export const attendanceApi = {
  logs: {
    list: (params?: Record<string, string>) => api.get('/attendance/logs/', { params }),
    punchIn: (formData: FormData) =>
      api.post('/attendance/logs/punch_in/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    punchOut: (formData: FormData) =>
      api.post('/attendance/logs/punch_out/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
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
    generate: (data: Record<string, unknown>) => api.post('/payroll/runs/generate/', data),
  },
  payslips: { list: () => api.get('/payroll/payslips/') },
};

export const recruitmentApi = {
  jobs: {
    list: () => api.get('/recruitment/jobs/'),
    create: (data: Record<string, unknown>) => api.post('/recruitment/jobs/', data),
    update: (id: string, data: Record<string, unknown>) => api.put(`/recruitment/jobs/${id}/`, data),
    get: (id: string) => api.get(`/recruitment/jobs/${id}/`),
  },
  candidates: {
    list: () => api.get('/recruitment/candidates/'),
    create: (formData: FormData) =>
      api.post('/recruitment/candidates/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    match: (id: string) => api.post(`/recruitment/candidates/${id}/match/`),
    invite: (id: string, data?: { send_email?: boolean; expiry_minutes?: number }) =>
      api.post(`/recruitment/candidates/${id}/invite/`, data ?? {}),
  },
  interviews: { list: () => api.get('/recruitment/interviews/') },
  aiSessions: { list: () => api.get('/recruitment/ai-sessions/') },
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
