'use client';

import React, { useMemo, useState } from 'react';
import {
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell,
  Input, Button, Pagination, Spinner,
} from '@nextui-org/react';
import { Search, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react';
import ExportButton from '@/components/wfh/ExportButton';
import { TenantFilterSelect } from '@/components/audit/TenantFilterSelect';
import { ModuleFilterSelect } from '@/components/audit/ModuleFilterSelect';
import type { AuditFilters, Pagination as PaginationMeta } from '@/lib/auditApi';

export type AuditColumn = {
  key: string;
  label: string;
  render?: (row: Record<string, unknown>) => React.ReactNode;
};

type Props<T extends Record<string, unknown>> = {
  title: string;
  description?: string;
  columns: AuditColumn[];
  rows: T[];
  pagination?: PaginationMeta;
  loading?: boolean;
  filters: AuditFilters;
  onFiltersChange: (filters: AuditFilters) => void;
  onRefresh: () => void;
  exportFilename: string;
  showModuleFilter?: boolean;
  showTenantFilter?: boolean;
  metadataKey?: string;
  extraFilters?: React.ReactNode;
};

export function AuditLogTable<T extends Record<string, unknown>>({
  title,
  description,
  columns,
  rows,
  pagination,
  loading,
  filters,
  onFiltersChange,
  onRefresh,
  exportFilename,
  showModuleFilter = true,
  showTenantFilter = false,
  metadataKey = 'metadata',
  extraFilters,
}: Props<T>) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const exportRows = useMemo(
    () =>
      rows.map((row) => {
        const flat: Record<string, unknown> = {};
        columns.forEach((col) => {
          flat[col.label] = col.render ? col.render(row) : row[col.key];
        });
        if (row[metadataKey]) flat.metadata = JSON.stringify(row[metadataKey]);
        return flat;
      }),
    [rows, columns, metadataKey],
  );

  const toggleExpand = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="w-full flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-extrabold text-foreground">{title}</h1>
        {description && <p className="text-default-500 text-lg">{description}</p>}
      </div>

      <div className="flex flex-wrap gap-3 items-end">
        <Input
          className="max-w-xs"
          placeholder="Search..."
          startContent={<Search size={16} />}
          value={filters.search || ''}
          onValueChange={(v) => onFiltersChange({ ...filters, search: v, page: 1 })}
        />
        {showModuleFilter && (
          <ModuleFilterSelect
            value={filters.module || ''}
            onChange={(module) => onFiltersChange({ ...filters, module: module || undefined, page: 1 })}
          />
        )}
        <Input
          className="max-w-xs"
          placeholder="Action"
          value={filters.action || ''}
          onValueChange={(v) => onFiltersChange({ ...filters, action: v, page: 1 })}
        />
        <Input
          type="date"
          className="max-w-xs"
          label="From"
          value={filters.date_from?.slice(0, 10) || ''}
          onValueChange={(v) => onFiltersChange({ ...filters, date_from: v ? `${v}T00:00:00` : undefined, page: 1 })}
        />
        <Input
          type="date"
          className="max-w-xs"
          label="To"
          value={filters.date_to?.slice(0, 10) || ''}
          onValueChange={(v) => onFiltersChange({ ...filters, date_to: v ? `${v}T23:59:59` : undefined, page: 1 })}
        />
        {showTenantFilter && (
          <TenantFilterSelect
            value={filters.tenant_id || ''}
            onChange={(tenant_id) => onFiltersChange({ ...filters, tenant_id: tenant_id || undefined, page: 1 })}
          />
        )}
        {extraFilters}
        <Button isIconOnly variant="flat" onPress={onRefresh} aria-label="Refresh">
          <RefreshCw size={18} />
        </Button>
        <ExportButton data={exportRows} filename={exportFilename} />
        <ExportButton data={exportRows} filename={exportFilename} format="json" />
      </div>

      <div className="border border-divider rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center p-12"><Spinner /></div>
        ) : (
          <Table
            aria-label={title}
            removeWrapper
            classNames={{ wrapper: 'w-full min-w-full', table: 'w-full' }}
          >
            <TableHeader>
              <TableColumn width={40}> </TableColumn>
              {columns.map((col) => (
                <TableColumn key={col.key}>{col.label}</TableColumn>
              ))}
            </TableHeader>
            <TableBody emptyContent="No audit records found.">
              {rows.map((row) => {
                const id = String(row.id ?? row.created_at);
                const isOpen = expanded[id];
                return (
                  <React.Fragment key={id}>
                    <TableRow>
                      <TableCell>
                        {row[metadataKey] ? (
                          <button type="button" onClick={() => toggleExpand(id)} className="text-default-500">
                            {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                          </button>
                        ) : null}
                      </TableCell>
                      {columns.map((col) => (
                        <TableCell key={col.key}>
                          {col.render ? col.render(row) : String(row[col.key] ?? '—')}
                        </TableCell>
                      ))}
                    </TableRow>
                    {isOpen && row[metadataKey] ? (
                      <TableRow>
                        <TableCell>{null}</TableCell>
                        <TableCell colSpan={columns.length}>
                          <pre className="text-xs bg-default-100 p-3 rounded-lg overflow-x-auto">
                            {JSON.stringify(row[metadataKey], null, 2)}
                          </pre>
                        </TableCell>
                        {columns.slice(1).map((col) => (
                          <TableCell key={`meta-${col.key}`} className="hidden p-0 max-h-0">
                            {null}
                          </TableCell>
                        ))}
                      </TableRow>
                    ) : null}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        )}
      </div>

      {pagination && pagination.pages > 1 && (
        <div className="flex justify-center">
          <Pagination
            total={pagination.pages}
            page={pagination.page}
            onChange={(page) => onFiltersChange({ ...filters, page })}
          />
        </div>
      )}
    </div>
  );
}
