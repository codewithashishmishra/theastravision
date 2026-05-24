'use client';

import React, { useState, useMemo } from 'react';
import { 
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, 
  User, Chip, Button, Input, DropdownTrigger, Dropdown, DropdownMenu, 
  DropdownItem, Pagination, Select, SelectItem, useDisclosure,
  Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Spinner, Avatar
} from "@nextui-org/react";
import { Plus, Search, MoreVertical, Edit, Trash2, Eye, Building2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';

const API_URL = 'http://127.0.0.1:8000/api/v1/company-profiles/';

const columns = [
  {name: "COMPANY", uid: "legal_name"},
  {name: "REGISTRATION NO", uid: "registration_number"},
  {name: "TAX ID", uid: "tax_id"},
  {name: "ACTIONS", uid: "actions"},
];

export default function AllCompaniesPage() {
  const queryClient = useQueryClient();
  const [filterValue, setFilterValue] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState("10");

  // Modal controls
  const {isOpen, onOpen, onOpenChange} = useDisclosure();
  const {isOpen: isDeleteOpen, onOpen: onDeleteOpen, onOpenChange: onDeleteOpenChange} = useDisclosure();
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('create');
  const [selectedCompany, setSelectedCompany] = useState<any>(null);
  const [itemToDelete, setItemToDelete] = useState<any>(null);

  // Form State
  const [formData, setFormData] = useState({
    legal_name: '',
    registration_number: '',
    tax_id: '',
    website: '',
    logo: ''
  });

  // Query
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['companies', page, pageSize, filterValue],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const res = await api.get(API_URL, {
        params: {
          page: page,
          page_size: pageSize,
          search: filterValue
        }
      });
      return res.data;
    }
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (newCompany: any) => api.post(API_URL, newCompany),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      onOpenChange(); // close
    }
  });

  const updateMutation = useMutation({
    mutationFn: (updatedCompany: any) => api.put(`${API_URL}${selectedCompany.id}/`, updatedCompany),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      onOpenChange(); // close
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`${API_URL}${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    }
  });

  const totalPages = React.useMemo(() => {
    return data?.count ? Math.max(1, Math.ceil(Number(data.count) / Number(pageSize))) : 1;
  }, [data?.count, pageSize]);

  const handleOpenModal = (mode: 'create' | 'edit' | 'view', company: any = null) => {
    setModalMode(mode);
    setSelectedCompany(company);
    if (company) {
      setFormData({
        legal_name: company.legal_name || '',
        registration_number: company.registration_number || '',
        tax_id: company.tax_id || '',
        website: company.website || '',
        logo: company.logo || ''
      });
    } else {
      setFormData({ legal_name: '', registration_number: '', tax_id: '', website: '', logo: '' });
    }
    onOpen();
  };

  const handleSave = () => {
    if (modalMode === 'create') {
      createMutation.mutate(formData);
    } else if (modalMode === 'edit') {
      updateMutation.mutate(formData);
    }
  };

  const renderCell = React.useCallback((company: any, columnKey: React.Key) => {
    const cellValue = company[columnKey as keyof typeof company];

    switch (columnKey) {
      case "legal_name":
        return (
          <User
            avatarProps={{
              radius: "lg", 
              src: company.logo,
              showFallback: true,
              fallback: <Building2 size={20} className="text-default-400" />,
              className: "bg-default-200/50"
            }}
            description={
              company.website ? (
                <a 
                  href={company.website.startsWith('http') ? company.website : `https://${company.website}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary hover:underline hover:text-primary-500 transition-colors z-20 relative block mt-0.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  {company.website}
                </a>
              ) : (
                <span className="text-default-500 mt-0.5 block">
                  {company.registration_number || 'No additional info'}
                </span>
              )
            }
            name={cellValue}
          >
            {cellValue}
          </User>
        );
      case "actions":
        return (
          <div className="relative flex justify-end items-center gap-2">
            <Dropdown>
              <DropdownTrigger>
                <Button isIconOnly size="sm" variant="light">
                  <MoreVertical className="text-default-300" size={18} />
                </Button>
              </DropdownTrigger>
              <DropdownMenu aria-label="Company Actions">
                <DropdownItem startContent={<Eye size={16} />} onClick={() => handleOpenModal('view', company)}>
                  View Details
                </DropdownItem>
                <DropdownItem startContent={<Edit size={16} />} onClick={() => handleOpenModal('edit', company)}>
                  Edit Company
                </DropdownItem>
                <DropdownItem 
                  className="text-danger" 
                  color="danger" 
                  startContent={<Trash2 size={16} />}
                  onClick={() => {
                    setItemToDelete(company);
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
        return cellValue || '-';
    }
  }, []);

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground">All Companies</h1>
          <p className="text-sm text-default-500 mt-1">Manage all tenant organizations on the platform.</p>
        </div>
        <Button color="primary" endContent={<Plus size={18} />} className="font-bold shadow-lg shadow-primary/30" onClick={() => handleOpenModal('create')}>
          Add New Company
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
            placeholder="Search by name or registration..."
            startContent={<Search className="text-default-300" size={18} />}
            value={filterValue}
            onClear={() => setFilterValue("")}
            onValueChange={(val) => {
              setFilterValue(val);
              setPage(1); // reset to page 1 on search
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
              onChange={(e) => {
                setPageSize(e.target.value);
                setPage(1); // reset page when page size changes
              }}
              variant="bordered"
            >
              {['10', '20', '50', '100', '500'].map(size => (
                <SelectItem key={size} value={size}>{size}</SelectItem>
              ))}
            </Select>
          </div>
        </div>

        <div className="w-full overflow-x-auto custom-scrollbar pb-4">
          <Table 
            aria-label="Companies Table" 
            shadow="none"
            isHeaderSticky
            onRowAction={(key) => {
              const company = data?.results.find((c: any) => c.id === key || c.id === Number(key));
              if (company) handleOpenModal('view', company);
            }}
            classNames={{
              base: "max-h-[60vh] min-w-full",
              wrapper: "p-0 border-none bg-transparent",
              th: "bg-default-100/80 backdrop-blur-md text-default-700 font-extrabold tracking-wider z-10 py-4 uppercase text-xs",
              td: "py-4 border-b border-default-100 font-medium",
              tr: "hover:bg-primary/5 cursor-pointer transition-colors group"
            }}
          >
            <TableHeader columns={columns}>
              {(column) => (
                <TableColumn key={column.uid} align={column.uid === "actions" ? "center" : "start"}>
                  {column.name}
                </TableColumn>
              )}
            </TableHeader>
            <TableBody 
              items={data?.results || []} 
              isLoading={isLoading || isFetching}
              loadingContent={
                <div className="absolute inset-0 bg-background/40 backdrop-blur-sm flex items-center justify-center z-50 rounded-xl">
                  <Spinner label="Loading Companies..." color="primary" size="lg" />
                </div>
              }
              emptyContent={isLoading ? " " : "No companies found"}
            >
              {(item: any) => (
                <TableRow key={item.id}>
                  {(columnKey) => <TableCell>{renderCell(item, columnKey)}</TableCell>}
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        <div className="flex w-full justify-between items-center mt-6 pt-4 border-t border-divider">
          <span className="text-small text-default-500 font-medium">
            Total <span className="text-foreground font-bold">{data?.count || 0}</span> companies
          </span>
          
          <div className="flex items-center gap-2">
            <Button 
              size="sm" 
              variant="flat" 
              color="primary"
              isDisabled={page === 1} 
              onPress={() => setPage(1)}
            >
              First
            </Button>
            <Button 
              size="sm" 
              variant="flat" 
              color="primary"
              isDisabled={page === 1} 
              onPress={() => setPage(p => Math.max(1, p - 1))}
            >
              Prev
            </Button>
            
            <span className="text-small font-semibold mx-2">
              Page {page} of {totalPages}
            </span>
            
            <Button 
              size="sm" 
              variant="flat" 
              color="primary"
              isDisabled={page === totalPages || totalPages === 0} 
              onPress={() => setPage(p => Math.min(totalPages, p + 1))}
            >
              Next
            </Button>
            <Button 
              size="sm" 
              variant="flat" 
              color="primary"
              isDisabled={page === totalPages || totalPages === 0} 
              onPress={() => setPage(totalPages)}
            >
              Last
            </Button>
          </div>
        </div>
      </motion.div>

      {/* CRUD Modal */}
      <Modal isOpen={isOpen} onOpenChange={onOpenChange} size="2xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                {modalMode === 'create' && 'Add New Company'}
                {modalMode === 'edit' && 'Edit Company'}
                {modalMode === 'view' && 'Company Details'}
              </ModalHeader>
              <ModalBody>
                <div className="grid grid-cols-2 gap-4">
                  <Input 
                    label="Legal Name" 
                    variant="bordered" 
                    value={formData.legal_name} 
                    onChange={(e) => setFormData({...formData, legal_name: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Input 
                    label="Registration Number" 
                    variant="bordered" 
                    value={formData.registration_number} 
                    onChange={(e) => setFormData({...formData, registration_number: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Input 
                    label="Tax ID" 
                    variant="bordered" 
                    value={formData.tax_id} 
                    onChange={(e) => setFormData({...formData, tax_id: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Input 
                    label="Website" 
                    variant="bordered" 
                    value={formData.website} 
                    onChange={(e) => setFormData({...formData, website: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <div className="flex gap-4 items-center col-span-2">
                    <Avatar 
                      key={formData.logo || 'fallback'}
                      radius="md"
                      className="w-14 h-14 bg-default-200/50"
                      src={formData.logo}
                      showFallback
                      fallback={<Building2 size={24} className="text-default-400" />}
                    />
                    <Input 
                      label="Logo URL" 
                      variant="bordered" 
                      placeholder="https://..."
                      value={formData.logo} 
                      className="flex-1"
                      onChange={(e) => setFormData({...formData, logo: e.target.value})}
                      isReadOnly={modalMode === 'view'}
                    />
                  </div>
                </div>
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={onClose}>
                  {modalMode === 'view' ? 'Close' : 'Cancel'}
                </Button>
                {modalMode !== 'view' && (
                  <Button 
                    color="primary" 
                    onPress={handleSave} 
                    isLoading={createMutation.isPending || updateMutation.isPending}
                  >
                    Save Changes
                  </Button>
                )}
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteOpen} onOpenChange={onDeleteOpenChange} size="md" backdrop="blur">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1 text-danger font-bold text-xl">Confirm Deletion</ModalHeader>
              <ModalBody>
                <div className="flex flex-col gap-4 pb-2">
                  <div className="w-16 h-16 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto mb-2 animate-pulse">
                    <Trash2 size={32} />
                  </div>
                  <p className="text-center font-extrabold text-lg text-foreground">Are you absolutely sure?</p>
                  <p className="text-center text-default-500 text-sm leading-relaxed">
                    You are about to permanently delete <strong className="text-foreground">{itemToDelete?.legal_name}</strong>. 
                    This action cannot be undone and all associated data will be wiped entirely.
                  </p>
                  
                  {/* Interactive Tip */}
                  <div className="bg-warning/10 border border-warning/20 rounded-xl p-4 mt-2 flex gap-3 items-start shadow-inner">
                    <span className="text-warning mt-0.5 text-lg">💡</span>
                    <p className="text-xs text-warning-600 dark:text-warning-500 font-medium leading-relaxed">
                      <strong>Pro Tip:</strong> Instead of deleting, consider editing the company profile and changing its status to "Inactive" to preserve historical records.
                    </p>
                  </div>
                </div>
              </ModalBody>
              <ModalFooter className="flex justify-center gap-4 pb-6 pt-2">
                <Button variant="flat" onPress={onClose} className="font-semibold w-24">
                  Cancel
                </Button>
                <Button 
                  color="danger" 
                  className="font-bold w-24 shadow-lg shadow-danger/30"
                  isLoading={deleteMutation.isPending}
                  onPress={() => {
                    deleteMutation.mutate(itemToDelete?.id);
                    onClose();
                  }}
                >
                  Delete
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

    </div>
  );
}
