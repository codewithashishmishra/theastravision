'use client';

import { useCallback, useEffect, useState } from 'react';
import { AuditLogTable } from '@/components/audit/AuditLogTable';
import { wfhApi } from '@/lib/wfhApi';
import type { AuditFilters } from '@/lib/auditApi';
import { formatUtcDateTime } from '@/lib/formatDateTime';

const columns = [
  { key: 'created_at', label: 'Time', render: (row: Record<string, unknown>) => formatUtcDateTime(String(row.created_at)) },
  { key: 'action', label: 'Action' },
  { key: 'entity_type', label: 'Entity' },
  { key: 'ip_address', label: 'IP' },
];

export default function TrackerAuditLogsPage() {
  const [filters, setFilters] = useState<AuditFilters>({ page: 1, page_size: 50 });
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 50, total: 0, pages: 1 });
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    wfhApi.auditLogs(filters)
      .then((r) => {
        setRows(r.data.results || r.data);
        if (r.data.pagination) setPagination(r.data.pagination);
      })
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  return (
    <AuditLogTable
      title="Tracker Audit Logs"
      description="WFH desktop tracker actions for your tenant."
      columns={columns}
      rows={rows}
      pagination={pagination}
      loading={loading}
      filters={filters}
      onFiltersChange={setFilters}
      onRefresh={load}
      exportFilename="tracker-audit-logs"
      showModuleFilter={false}
    />
  );
}
