'use client';

import { useCallback, useEffect, useState } from 'react';
import { AuditLogTable } from '@/components/audit/AuditLogTable';
import { auditApi, type AuditFilters, type AuditLog } from '@/lib/auditApi';
import { formatUtcDateTime } from '@/lib/formatDateTime';

const columns = [
  { key: 'created_at', label: 'Time', render: (row: Record<string, unknown>) => formatUtcDateTime(String(row.created_at)) },
  { key: 'tenant_name', label: 'Tenant' },
  { key: 'user_email', label: 'User' },
  { key: 'module', label: 'Module' },
  { key: 'action', label: 'Action' },
  { key: 'ip_address', label: 'IP' },
];

export default function PlatformAuditPage() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1, page_size: 50 });
  const [rows, setRows] = useState<AuditLog[]>([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 50, total: 0, pages: 1 });
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    auditApi.platformLogs(filters)
      .then((res) => {
        setRows(res.data.results);
        setPagination(res.data.pagination);
      })
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  return (
    <AuditLogTable
      title="Platform Audit Logs"
      description="Cross-tenant compliance audit trail for Super Admin."
      columns={columns}
      rows={rows as unknown as Record<string, unknown>[]}
      pagination={pagination}
      loading={loading}
      filters={filters}
      onFiltersChange={setFilters}
      onRefresh={load}
      exportFilename="platform-audit-logs"
      showTenantFilter
    />
  );
}
