'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell,
  User, Chip, Button, Input, DropdownTrigger, Dropdown, DropdownMenu,
  DropdownItem, Select, SelectItem, useDisclosure,
  Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Spinner,
} from '@nextui-org/react';
import { Plus, Search, MoreVertical, Edit, Trash2, Eye, Building2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import api from '@/lib/axios';
import { motion } from 'framer-motion';

type Tenant = {
  id: string;
  name: string;
  domain: string;
  email_domain: string | null;
  subscription_plan: string;
  default_currency: string;
  is_active: boolean;
  enabled_jurisdictions: string[];
};

const columns = [
  { name: 'TENANT', uid: 'name' },
  { name: 'DOMAIN', uid: 'domain' },
  { name: 'PLAN', uid: 'subscription_plan' },
  { name: 'STATUS', uid: 'is_active' },
  { name: 'ACTIONS', uid: 'actions' },
];

export default function AllCompaniesPage() {
  const queryClient = useQueryClient();
  const [filterValue, setFilterValue] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState('10');

  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onOpenChange: onDeleteOpenChange } = useDisclosure();
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('create');
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [itemToDelete, setItemToDelete] = useState<Tenant | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    email_domain: '',
    subscription_plan: 'starter',
    default_currency: 'INR',
    is_active: true,
  });

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['tenants', page, pageSize, filterValue],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const res = await api.get('/tenants/', {
        params: { page, page_size: pageSize, search: filterValue || undefined },
      });
      return res.data as { count: number; results: Tenant[] };
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.post('/tenants/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      onOpenChange();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.patch(`/tenants/${selectedTenant!.id}/`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      onOpenChange();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/tenants/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
    },
  });

  const totalPages = useMemo(() => {
    return data?.count ? Math.max(1, Math.ceil(Number(data.count) / Number(pageSize))) : 1;
  }, [data?.count, pageSize]);

  const handleOpenModal = (mode: 'create' | 'edit' | 'view', tenant: Tenant | null = null) => {
    setModalMode(mode);
    setSelectedTenant(tenant);
    if (tenant) {
      setFormData({
        name: tenant.name || '',
        domain: tenant.domain || '',
        email_domain: tenant.email_domain || '',
        subscription_plan: tenant.subscription_plan || 'starter',
        default_currency: tenant.default_currency || 'INR',
        is_active: tenant.is_active,
      });
    } else {
      setFormData({
        name: '',
        domain: '',
        email_domain: '',
        subscription_plan: 'starter',
        default_currency: 'INR',
        is_active: true,
      });
    }
    onOpen();
  };

  const handleSave = () => {
    const payload = {
      ...formData,
      enabled_jurisdictions: ['IN'],
    };
    if (modalMode === 'create') {
      createMutation.mutate(payload);
    } else if (modalMode === 'edit') {
      updateMutation.mutate(payload);
    }
  };

  const renderCell = useCallback((tenant: Tenant, columnKey: React.Key) => {
    switch (columnKey) {
      case 'name':
        return (
          <User
            avatarProps={{
              radius: 'lg',
              showFallback: true,
              fallback: <Building2 size={20} className="text-default-400" />,
              className: 'bg-default-200/50',
            }}
            description={tenant.email_domain || tenant.domain}
            name={tenant.name}
          />
        );
      case 'domain':
        return tenant.domain || '—';
      case 'subscription_plan':
        return (
          <Chip size="sm" variant="flat" color="primary" className="capitalize">
            {tenant.subscription_plan}
          </Chip>
        );
      case 'is_active':
        return (
          <Chip size="sm" color={tenant.is_active ? 'success' : 'default'} variant="flat">
            {tenant.is_active ? 'Active' : 'Inactive'}
          </Chip>
        );
      case 'actions':
        return (
          <div className="relative flex justify-end items-center gap-2">
            <Dropdown>
              <DropdownTrigger>
                <Button isIconOnly size="sm" variant="light">
                  <MoreVertical className="text-default-300" size={18} />
                </Button>
              </DropdownTrigger>
              <DropdownMenu aria-label="Tenant Actions">
                <DropdownItem startContent={<Eye size={16} />} onPress={() => handleOpenModal('view', tenant)}>
                  View Details
                </DropdownItem>
                <DropdownItem startContent={<Edit size={16} />} onPress={() => handleOpenModal('edit', tenant)}>
                  Edit Tenant
                </DropdownItem>
                <DropdownItem
                  className="text-danger"
                  color="danger"
                  startContent={<Trash2 size={16} />}
                  onPress={() => {
                    setItemToDelete(tenant);
                    onDeleteOpen();
                  }}
                >
                  Delete Tenant
                </DropdownItem>
              </DropdownMenu>
            </Dropdown>
          </div>
        );
      default:
        return String(tenant[columnKey as keyof Tenant] ?? '—');
    }
  }, []);

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground">All Companies</h1>
          <p className="text-sm text-default-500 mt-1">Manage all tenant organizations on the platform.</p>
        </div>
        <Button color="primary" endContent={<Plus size={18} />} className="font-bold shadow-lg shadow-primary/30" onPress={() => handleOpenModal('create')}>
          Add New Tenant
        </Button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-content1/60 backdrop-blur-xl border border-divider rounded-3xl overflow-hidden p-6 shadow-2xl shadow-default/5"
      >
        <div className="flex justify-between items-center mb-6">
          <Input
            isClearable
            className="w-full sm:max-w-[44%]"
            placeholder="Search by name or domain..."
            startContent={<Search className="text-default-300" size={18} />}
            value={filterValue}
            onClear={() => setFilterValue('')}
            onValueChange={(val) => {
              setFilterValue(val);
              setPage(1);
            }}
            variant="faded"
            radius="lg"
          />
          <div className="flex items-center gap-3">
            <span className="text-sm text-default-500">Rows per page:</span>
            <Select
              className="w-24"
              size="sm"
              selectedKeys={[pageSize]}
              onSelectionChange={(keys) => {
                const val = Array.from(keys)[0] as string;
                if (val) {
                  setPageSize(val);
                  setPage(1);
                }
              }}
              variant="bordered"
            >
              {['10', '20', '50', '100'].map((size) => (
                <SelectItem key={size} value={size}>{size}</SelectItem>
              ))}
            </Select>
          </div>
        </div>

        <div className="w-full overflow-x-auto custom-scrollbar pb-4">
          <Table
            aria-label="Tenants Table"
            shadow="none"
            isHeaderSticky
            classNames={{
              base: 'max-h-[60vh] min-w-full',
              wrapper: 'p-0 border-none bg-transparent',
              th: 'bg-default-100/80 backdrop-blur-md text-default-700 font-extrabold tracking-wider z-10 py-4 uppercase text-xs',
              td: 'py-4 border-b border-default-100 font-medium',
              tr: 'hover:bg-primary/5 cursor-pointer transition-colors group',
            }}
          >
            <TableHeader columns={columns}>
              {(column) => (
                <TableColumn key={column.uid} align={column.uid === 'actions' ? 'center' : 'start'}>
                  {column.name}
                </TableColumn>
              )}
            </TableHeader>
            <TableBody
              items={data?.results || []}
              isLoading={isLoading || isFetching}
              loadingContent={
                <div className="absolute inset-0 bg-background/40 backdrop-blur-sm flex items-center justify-center z-50 rounded-xl">
                  <Spinner label="Loading tenants..." color="primary" size="lg" />
                </div>
              }
              emptyContent={isLoading ? ' ' : 'No tenants found'}
            >
              {(item: Tenant) => (
                <TableRow key={item.id}>
                  {(columnKey) => <TableCell>{renderCell(item, columnKey)}</TableCell>}
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        <div className="flex w-full justify-between items-center mt-6 pt-4 border-t border-divider">
          <span className="text-small text-default-500 font-medium">
            Total <span className="text-foreground font-bold">{data?.count || 0}</span> tenants
          </span>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="flat" color="primary" isDisabled={page === 1} onPress={() => setPage(1)}>First</Button>
            <Button size="sm" variant="flat" color="primary" isDisabled={page === 1} onPress={() => setPage((p) => Math.max(1, p - 1))}>Prev</Button>
            <span className="text-small font-semibold mx-2">Page {page} of {totalPages}</span>
            <Button size="sm" variant="flat" color="primary" isDisabled={page === totalPages || totalPages === 0} onPress={() => setPage((p) => Math.min(totalPages, p + 1))}>Next</Button>
            <Button size="sm" variant="flat" color="primary" isDisabled={page === totalPages || totalPages === 0} onPress={() => setPage(totalPages)}>Last</Button>
          </div>
        </div>
      </motion.div>

      <Modal isOpen={isOpen} onOpenChange={onOpenChange} size="2xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                {modalMode === 'create' && 'Add New Tenant'}
                {modalMode === 'edit' && 'Edit Tenant'}
                {modalMode === 'view' && 'Tenant Details'}
              </ModalHeader>
              <ModalBody>
                <div className="grid grid-cols-2 gap-4">
                  <Input label="Name" variant="bordered" value={formData.name} onValueChange={(v) => setFormData({ ...formData, name: v })} isReadOnly={modalMode === 'view'} />
                  <Input label="Domain" variant="bordered" value={formData.domain} onValueChange={(v) => setFormData({ ...formData, domain: v })} isReadOnly={modalMode === 'view'} />
                  <Input label="Email Domain" variant="bordered" value={formData.email_domain} onValueChange={(v) => setFormData({ ...formData, email_domain: v })} isReadOnly={modalMode === 'view'} />
                  <Select label="Plan" variant="bordered" selectedKeys={[formData.subscription_plan]} isDisabled={modalMode === 'view'} onSelectionChange={(keys) => { const v = Array.from(keys)[0] as string; if (v) setFormData({ ...formData, subscription_plan: v }); }}>
                    <SelectItem key="starter">Starter</SelectItem>
                    <SelectItem key="professional">Professional</SelectItem>
                    <SelectItem key="enterprise">Enterprise</SelectItem>
                  </Select>
                  <Input label="Default Currency" variant="bordered" value={formData.default_currency} onValueChange={(v) => setFormData({ ...formData, default_currency: v })} isReadOnly={modalMode === 'view'} />
                </div>
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={onClose}>{modalMode === 'view' ? 'Close' : 'Cancel'}</Button>
                {modalMode !== 'view' && (
                  <Button color="primary" onPress={handleSave} isLoading={createMutation.isPending || updateMutation.isPending}>Save Changes</Button>
                )}
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      <Modal isOpen={isDeleteOpen} onOpenChange={onDeleteOpenChange} size="md" backdrop="blur">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1 text-danger font-bold text-xl">Confirm Deletion</ModalHeader>
              <ModalBody>
                <p className="text-center text-default-500 text-sm">
                  Delete tenant <strong>{itemToDelete?.name}</strong>? This cannot be undone.
                </p>
              </ModalBody>
              <ModalFooter>
                <Button variant="flat" onPress={onClose}>Cancel</Button>
                <Button color="danger" isLoading={deleteMutation.isPending} onPress={() => { deleteMutation.mutate(itemToDelete!.id); onClose(); }}>Delete</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
