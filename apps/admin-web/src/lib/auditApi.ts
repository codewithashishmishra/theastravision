import api from './axios';

export type AuditLog = {
  id: string;
  tenant?: string | null;
  tenant_name?: string | null;
  user?: string | null;
  user_email?: string | null;
  action: string;
  module: string;
  ip_address?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
};

export type LoginSession = {
  id: number | string;
  user?: string;
  user_email?: string;
  tenant_id?: string | null;
  tenant_name?: string | null;
  client_type: string;
  device_fingerprint?: string;
  ip_address?: string;
  user_agent?: string;
  location_city?: string;
  location_country?: string;
  login_method: string;
  is_revoked: boolean;
  created_at: string;
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type AuditListResponse<T> = {
  results: T[];
  pagination: Pagination;
};

export type SystemLogEntry = {
  timestamp: string;
  level: string;
  service: string;
  message: string;
  raw: string;
  metadata: Record<string, unknown>;
};

export type AuditFilters = {
  page?: number;
  page_size?: number;
  module?: string;
  action?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  login_method?: string;
  client_type?: string;
  revoked?: string;
  tenant_id?: string;
  tenant_name?: string;
};

function buildParams(filters: AuditFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, String(value));
  });
  return params.toString();
}

export const auditApi = {
  platformLogs: (filters?: AuditFilters) =>
    api.get<AuditListResponse<AuditLog>>(`/audit/platform-logs/?${buildParams(filters)}`),
  adminActions: (filters?: AuditFilters) =>
    api.get<AuditListResponse<AuditLog>>(`/audit/admin-actions/?${buildParams(filters)}`),
  loginSessions: (filters?: AuditFilters) =>
    api.get<AuditListResponse<LoginSession>>(`/audit/login-sessions/?${buildParams(filters)}`),
  exportUrl: (type: 'platform' | 'admin' | 'login', filters?: AuditFilters, format: 'csv' | 'json' = 'csv') => {
    const params = buildParams({ ...filters });
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    return `${base}/audit/export/?type=${type}&format=${format}${params ? `&${params}` : ''}`;
  },
  platformMetrics: (range = '1h') => api.get(`/platform/metrics/?range=${range}`),
  platformServices: () => api.get<{ services: { service: string; state: string; uptime?: string; backend: string }[] }>('/platform/services/'),
  systemLogs: (params: { service?: string; since?: string; level?: string; search?: string; limit?: number; tenant_id?: string } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') qs.set(k, String(v)); });
    return api.get<{ results: SystemLogEntry[]; count: number }>(`/platform/system-logs/?${qs.toString()}`);
  },
  systemLogsExportUrl: (params: Record<string, string | number | undefined> = {}, format: 'csv' | 'json' = 'csv') => {
    const qs = new URLSearchParams({ format, ...Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)])) });
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    return `${base}/platform/system-logs/export/?${qs.toString()}`;
  },
};
