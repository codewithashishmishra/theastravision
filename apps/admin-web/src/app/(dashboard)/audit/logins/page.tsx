'use client';

import { useCallback, useEffect, useState } from 'react';
import { Select, SelectItem, Chip } from '@nextui-org/react';
import { AuditLogTable } from '@/components/audit/AuditLogTable';
import { auditApi, type AuditFilters, type LoginSession } from '@/lib/auditApi';

const columns = [
  { key: 'created_at', label: 'Time', render: (row: Record<string, unknown>) => new Date(String(row.created_at)).toLocaleString() },
  { key: 'tenant_name', label: 'Tenant' },
  { key: 'user_email', label: 'User' },
  { key: 'login_method', label: 'Method' },
  { key: 'client_type', label: 'Client' },
  { key: 'ip_address', label: 'IP' },
  { key: 'location_city', label: 'Location', render: (row: Record<string, unknown>) => `${row.location_city || '—'}, ${row.location_country || '—'}` },
  { key: 'is_revoked', label: 'Status', render: (row: Record<string, unknown>) => (
    <Chip size="sm" color={row.is_revoked ? 'danger' : 'success'} variant="flat">
      {row.is_revoked ? 'Revoked' : 'Active'}
    </Chip>
  ) },
];

export default function LoginAuditPage() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1, page_size: 50 });
  const [rows, setRows] = useState<LoginSession[]>([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 50, total: 0, pages: 1 });
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    auditApi.loginSessions(filters)
      .then((res) => {
        setRows(res.data.results);
        setPagination(res.data.pagination);
      })
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const extraFilters = (
    <>
      <Select
        className="max-w-xs"
        label="Login method"
        selectedKeys={filters.login_method ? [filters.login_method] : []}
        onSelectionChange={(keys) => {
          const v = Array.from(keys)[0] as string | undefined;
          setFilters({ ...filters, login_method: v || undefined, page: 1 });
        }}
      >
        {['password', 'totp', 'passkey', 'face_scan'].map((m) => (
          <SelectItem key={m}>{m}</SelectItem>
        ))}
      </Select>
      <Select
        className="max-w-xs"
        label="Client"
        selectedKeys={filters.client_type ? [filters.client_type] : []}
        onSelectionChange={(keys) => {
          const v = Array.from(keys)[0] as string | undefined;
          setFilters({ ...filters, client_type: v || undefined, page: 1 });
        }}
      >
        {['web', 'tracker'].map((m) => (
          <SelectItem key={m}>{m}</SelectItem>
        ))}
      </Select>
    </>
  );

  return (
    <AuditLogTable
      title="Login Logs"
      description="Authentication sessions with IP, geo, and method."
      columns={columns}
      rows={rows as unknown as Record<string, unknown>[]}
      pagination={pagination}
      loading={loading}
      filters={filters}
      onFiltersChange={setFilters}
      onRefresh={load}
      exportFilename="login-sessions"
      showModuleFilter={false}
      showTenantFilter
      metadataKey="__none__"
      extraFilters={extraFilters}
    />
  );
}
