'use client';

import React, { useState, useMemo } from 'react';
import {
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell,
  Button, Input, Spinner, Chip, Pagination,
} from '@nextui-org/react';
import { Plus, Search, RefreshCw, Trash2, Edit } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';
import { parseApiError } from '@/lib/parseApiError';
import { AxiosError } from 'axios';
import { FormModal, FormField } from './FormModal';
import { ConfirmDeleteModal } from './ConfirmDeleteModal';

export type ColumnDef = {
  key: string;
  label: string;
  render?: (row: Record<string, unknown>) => React.ReactNode;
};

export type ResourcePageConfig = {
  title: string;
  description?: string;
  endpoint: string;
  queryKey: string;
  columns: ColumnDef[];
  formFields?: FormField[];
  readOnly?: boolean;
  searchPlaceholder?: string;
};

export function ResourcePage({ config }: { config: ResourcePageConfig }) {
  const queryClient = useQueryClient();
  const isAuthReady = useAuthReady();
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [saveError, setSaveError] = useState<string | null>(null);

  const { data, isLoading, isFetching, refetch, error } = useQuery({
    queryKey: [config.queryKey, page, filter],
    enabled: isAuthReady,
    queryFn: async () => {
      const params: Record<string, string | number> = { page };
      if (filter) params.search = filter;
      const res = await api.get(config.endpoint, { params });
      return res.data;
    },
  });

  const errorMessage = error
    ? error instanceof AxiosError && error.response?.status === 401
      ? 'Session expired — please sign in again.'
      : parseApiError(error, 'Failed to load data')
    : null;

  const rows = useMemo(() => unwrapList<Record<string, unknown>>(data ?? []), [data]);
  const total = typeof data === 'object' && data && 'count' in data ? (data as { count: number }).count : rows.length;

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (editId) {
        return api.put(`${config.endpoint}${editId}/`, formData);
      }
      return api.post(config.endpoint, formData);
    },
    onSuccess: () => {
      setSaveError(null);
      queryClient.invalidateQueries({ queryKey: [config.queryKey] });
      setModalOpen(false);
      setEditId(null);
      setFormData({});
    },
    onError: (err) => {
      setSaveError(parseApiError(err, 'Failed to save'));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`${config.endpoint}${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [config.queryKey] });
      setDeleteId(null);
    },
  });

  const openCreate = () => {
    setEditId(null);
    setFormData({});
    setSaveError(null);
    setModalOpen(true);
  };

  const openEdit = (row: Record<string, unknown>) => {
    setSaveError(null);
    setEditId(String(row.id));
    const initial: Record<string, string> = {};
    config.formFields?.forEach((f) => {
      initial[f.key] = row[f.key] != null ? String(row[f.key]) : '';
    });
    setFormData(initial);
    setModalOpen(true);
  };

  const tableColumns = config.readOnly
    ? config.columns
    : [...config.columns, { key: 'actions', label: 'ACTIONS' }];

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground">{config.title}</h1>
          {config.description && <p className="text-sm text-default-500 mt-1">{config.description}</p>}
        </div>
        <div className="flex gap-2">
          <Button isIconOnly variant="flat" onPress={() => refetch()} isLoading={isFetching}>
            <RefreshCw size={18} />
          </Button>
          {!config.readOnly && config.formFields && (
            <Button color="primary" startContent={<Plus size={18} />} onPress={openCreate}>Add New</Button>
          )}
        </div>
      </div>

      {errorMessage && (
        <Chip color="danger" variant="flat">{errorMessage}</Chip>
      )}

      <div className="flex gap-4 items-center">
        <Input
          className="max-w-sm"
          placeholder={config.searchPlaceholder ?? 'Search...'}
          startContent={<Search size={16} />}
          value={filter}
          onValueChange={setFilter}
          isClearable
        />
      </div>

      <Table aria-label={config.title} classNames={{ wrapper: 'border border-divider shadow-sm' }}>
        <TableHeader>
          {tableColumns.map((col) => (
            <TableColumn key={col.key}>{col.label}</TableColumn>
          ))}
        </TableHeader>
        <TableBody
          emptyContent={isLoading ? <Spinner /> : 'No records found'}
          items={rows}
        >
          {(row) => (
            <TableRow key={String(row.id)}>
              {tableColumns.map((col) => {
                if (col.key === 'actions') {
                  return (
                    <TableCell key="actions">
                      <div className="flex gap-1">
                        <Button isIconOnly size="sm" variant="light" onPress={() => openEdit(row)}>
                          <Edit size={16} />
                        </Button>
                        <Button
                          isIconOnly
                          size="sm"
                          variant="light"
                          color="danger"
                          onPress={() => { setDeleteId(String(row.id)); setDeleteOpen(true); }}
                        >
                          <Trash2 size={16} />
                        </Button>
                      </div>
                    </TableCell>
                  );
                }
                return (
                  <TableCell key={col.key}>
                    {col.render ? col.render(row) : String(row[col.key] ?? '—')}
                  </TableCell>
                );
              })}
            </TableRow>
          )}
        </TableBody>
      </Table>

      {total > 10 && (
        <Pagination total={Math.ceil(total / 10)} page={page} onChange={setPage} />
      )}

      {saveError && (
        <Chip color="danger" variant="flat">{saveError}</Chip>
      )}

      {config.formFields && (
        <FormModal
          isOpen={modalOpen}
          onOpenChange={setModalOpen}
          title={editId ? `Edit ${config.title}` : `Add ${config.title}`}
          fields={config.formFields}
          formData={formData}
          onChange={(k, v) => setFormData((p) => ({ ...p, [k]: v }))}
          onSubmit={() => saveMutation.mutate()}
          isLoading={saveMutation.isPending}
          isDisabled={saveMutation.isPending}
        />
      )}

      <ConfirmDeleteModal
        isOpen={deleteOpen}
        onOpenChange={setDeleteOpen}
        onConfirm={() => deleteId && deleteMutation.mutate(deleteId)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
