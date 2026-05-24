'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { 
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, 
  User, Chip, Button, Input, DropdownTrigger, Dropdown, DropdownMenu, 
  DropdownItem, Pagination, Select, SelectItem, useDisclosure,
  Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Spinner, Avatar
} from "@nextui-org/react";
import { Plus, Search, MoreVertical, Edit, Trash2, Eye, User as UserIcon } from 'lucide-react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import api from '@/lib/axios';
import { motion } from 'framer-motion';
import { unwrapList } from '@/lib/hrmsApi';

const API_URL = '/employees/employees/';

const columns = [
  {name: "EMPLOYEE", uid: "employee"},
  {name: "EMP CODE", uid: "employee_code"},
  {name: "GENDER", uid: "gender"},
  {name: "JOINING DATE", uid: "date_of_joining"},
  {name: "STATUS", uid: "status"},
  {name: "ACTIONS", uid: "actions"},
];

const statusColorMap: Record<string, "success" | "danger" | "warning"> = {
  Active: "success",
  Terminated: "danger",
  Suspended: "warning",
};

export default function EmployeeDirectoryPage() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const [filterValue, setFilterValue] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState("10");

  // Modal controls
  const {isOpen, onOpen, onOpenChange} = useDisclosure();
  const {isOpen: isDeleteOpen, onOpen: onDeleteOpen, onOpenChange: onDeleteOpenChange} = useDisclosure();
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('create');
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const [itemToDelete, setItemToDelete] = useState<any>(null);

  // Form State
  const [formData, setFormData] = useState({
    employee_code: '',
    first_name: '',
    last_name: '',
    gender: 'Male',
    date_of_joining: '',
    status: 'Active',
    avatar_url: '',
    employee_type: '',
    branch: '',
    reporting_manager: '',
  });
  const [saveError, setSaveError] = useState('');

  // Query
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['employees', page, pageSize, filterValue],
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
  const { data: employeeTypesData } = useQuery({
    queryKey: ['employee-types-for-employee-form'],
    queryFn: async () => (await api.get('/employees/employee-types/')).data,
  });
  const { data: branchesData } = useQuery({
    queryKey: ['branches-for-employee-form'],
    queryFn: async () => (await api.get('/branches/')).data,
  });
  const { data: managerOptionsData } = useQuery({
    queryKey: ['employees-manager-options'],
    queryFn: async () =>
      (await api.get(API_URL, { params: { page_size: 500, status: 'Active' } })).data,
  });
  const employeeTypes = unwrapList<any>(employeeTypesData ?? []);
  const branches = unwrapList<any>(branchesData ?? []);
  const managerOptions = unwrapList<any>(managerOptionsData ?? []).filter(
    (e: { id: string }) => !selectedEmployee || String(e.id) !== String(selectedEmployee.id)
  );
  const tenantHasEmployees =
    (managerOptionsData?.count ?? 0) > 0 || managerOptions.length > 0;

  // Mutations
  const createMutation = useMutation({
    mutationFn: (newEmp: any) => api.post(API_URL, newEmp),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      onOpenChange(); 
    }
  });

  const updateMutation = useMutation({
    mutationFn: (updatedEmp: any) => api.put(`${API_URL}${selectedEmployee.id}/`, updatedEmp),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      onOpenChange(); 
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`${API_URL}${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    }
  });

  const totalPages = React.useMemo(() => {
    return data?.count ? Math.max(1, Math.ceil(Number(data.count) / Number(pageSize))) : 1;
  }, [data?.count, pageSize]);

  const handleOpenModal = (mode: 'create' | 'edit' | 'view', employee: any = null) => {
    setModalMode(mode);
    setSelectedEmployee(employee);
    if (employee) {
      setFormData({
        employee_code: employee.employee_code || '',
        first_name: employee.first_name || '',
        last_name: employee.last_name || '',
        gender: employee.gender || 'Male',
        date_of_joining: employee.date_of_joining || '',
        status: employee.status || 'Active',
        avatar_url: employee.avatar_url || '',
        employee_type: employee.employee_type || '',
        branch: employee.branch || '',
        reporting_manager: employee.reporting_manager ? String(employee.reporting_manager) : '',
      });
    } else {
      setFormData({ 
        employee_code: `EMP-${Math.floor(Math.random() * 90000) + 10000}`, 
        first_name: '', 
        last_name: '', 
        gender: 'Male', 
        date_of_joining: new Date().toISOString().split('T')[0], 
        status: 'Active',
        avatar_url: '',
        employee_type: '',
        branch: '',
        reporting_manager: '',
      });
    }
    setSaveError('');
    onOpen();
  };

  useEffect(() => {
    if (searchParams.get('action') === 'create') {
      handleOpenModal('create');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const managerLabel = (emp: {
    first_name: string;
    last_name: string;
    employee_code: string;
    designation_name?: string;
  }) => {
    const desig = emp.designation_name ? ` — ${emp.designation_name}` : '';
    return `${emp.first_name} ${emp.last_name} (${emp.employee_code})${desig}`;
  };

  const buildPayload = () => {
    const payload: Record<string, unknown> = {
      employee_code: formData.employee_code,
      first_name: formData.first_name,
      last_name: formData.last_name,
      gender: formData.gender,
      date_of_joining: formData.date_of_joining,
      status: formData.status,
      employee_type: formData.employee_type || null,
      branch: formData.branch || null,
    };
    if (formData.reporting_manager) {
      payload.reporting_manager = formData.reporting_manager;
    } else if (tenantHasEmployees && modalMode !== 'view') {
      payload.reporting_manager = null;
    }
    return payload;
  };

  const handleSave = () => {
    if (!formData.employee_type) {
      return;
    }
    if (tenantHasEmployees && !formData.reporting_manager && modalMode === 'create') {
      setSaveError('Reporting manager is required.');
      return;
    }
    setSaveError('');
    const payload = buildPayload();
    if (modalMode === 'create') {
      createMutation.mutate(payload, {
        onError: (err: { response?: { data?: Record<string, string | string[]> } }) => {
          const data = err.response?.data;
          const msg =
            (typeof data?.reporting_manager === 'string' ? data.reporting_manager : null) ||
            (Array.isArray(data?.reporting_manager) ? data.reporting_manager[0] : null) ||
            'Failed to save employee.';
          setSaveError(msg);
        },
      });
    } else if (modalMode === 'edit') {
      updateMutation.mutate(payload, {
        onError: (err: { response?: { data?: Record<string, string | string[]> } }) => {
          const data = err.response?.data;
          const msg =
            (typeof data?.reporting_manager === 'string' ? data.reporting_manager : null) ||
            (Array.isArray(data?.reporting_manager) ? data.reporting_manager[0] : null) ||
            'Failed to update employee.';
          setSaveError(msg);
        },
      });
    }
  };

  const renderCell = React.useCallback((employee: any, columnKey: React.Key) => {
    const cellValue = employee[columnKey as keyof typeof employee];

    switch (columnKey) {
      case "employee":
        return (
          <User
            avatarProps={{
              radius: "lg", 
              src: employee.avatar_url,
              showFallback: true,
              fallback: <UserIcon size={20} className="text-default-400" />,
              className: "bg-default-200/50"
            }}
            description={employee.email || `${employee.first_name.toLowerCase()}.${employee.last_name.toLowerCase()}@company.com`}
            name={`${employee.first_name} ${employee.last_name}`}
          >
            {`${employee.first_name} ${employee.last_name}`}
          </User>
        );
      case "employee_code":
        return (
          <div className="flex flex-col">
            <p className="text-bold text-sm font-mono">{cellValue}</p>
          </div>
        );
      case "date_of_joining":
        return (
          <div className="flex flex-col">
            <p className="text-bold text-sm">{cellValue}</p>
          </div>
        );
      case "status":
        return (
          <Chip className="capitalize" color={statusColorMap[employee.status || 'Active']} size="sm" variant="flat">
            {employee.status || 'Active'}
          </Chip>
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
              <DropdownMenu aria-label="Employee Actions">
                <DropdownItem key="view" startContent={<Eye size={16} />} onClick={() => handleOpenModal('view', employee)}>
                  View Profile
                </DropdownItem>
                <DropdownItem key="edit" startContent={<Edit size={16} />} onClick={() => handleOpenModal('edit', employee)}>
                  Edit Details
                </DropdownItem>
                <DropdownItem 
                  key="delete"
                  className="text-danger" 
                  color="danger" 
                  startContent={<Trash2 size={16} />}
                  onClick={() => {
                    setItemToDelete(employee);
                    onDeleteOpen();
                  }}
                >
                  Delete Employee
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
          <h1 className="text-2xl font-extrabold text-foreground">Employee Directory</h1>
          <p className="text-sm text-default-500 mt-1">Manage and view all employee records across tenants.</p>
        </div>
        <Button color="primary" endContent={<Plus size={18} />} className="font-bold shadow-lg shadow-primary/30" onClick={() => handleOpenModal('create')}>
          Add New Employee
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
            placeholder="Search by name, code, or email..."
            startContent={<Search className="text-default-300" size={18} />}
            value={filterValue}
            onClear={() => setFilterValue("")}
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
              onChange={(e) => {
                setPageSize(e.target.value);
                setPage(1);
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
            aria-label="Employees Table" 
            shadow="none"
            isHeaderSticky
            onRowAction={(key) => {
              const employee = data?.results.find((e: any) => e.id === key || e.id === Number(key));
              if (employee) handleOpenModal('view', employee);
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
                  <Spinner label="Loading Employees..." color="primary" size="lg" />
                </div>
              }
              emptyContent={isLoading ? " " : "No employees found"}
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
            Total <span className="text-foreground font-bold">{data?.count || 0}</span> employees
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
                {modalMode === 'create' && 'Add New Employee'}
                {modalMode === 'edit' && 'Edit Employee Details'}
                {modalMode === 'view' && 'Employee Profile'}
              </ModalHeader>
              <ModalBody>
                <div className="flex justify-center mb-4">
                  <Avatar 
                    key={formData.avatar_url || 'fallback'}
                    radius="lg"
                    className="w-24 h-24 bg-default-200/50"
                    src={formData.avatar_url || ''}
                    showFallback
                    fallback={<UserIcon size={40} className="text-default-400" />}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Input 
                    label="First Name" 
                    variant="bordered" 
                    value={formData.first_name} 
                    onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Input 
                    label="Last Name" 
                    variant="bordered" 
                    value={formData.last_name} 
                    onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Input 
                    label="Employee Code" 
                    variant="bordered" 
                    value={formData.employee_code} 
                    onChange={(e) => setFormData({...formData, employee_code: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Select 
                    label="Gender" 
                    variant="bordered" 
                    selectedKeys={[formData.gender]} 
                    onChange={(e) => setFormData({...formData, gender: e.target.value})}
                    isDisabled={modalMode === 'view'}
                  >
                    <SelectItem key="Male" value="Male">Male</SelectItem>
                    <SelectItem key="Female" value="Female">Female</SelectItem>
                    <SelectItem key="Other" value="Other">Other</SelectItem>
                  </Select>
                  <Input 
                    label="Date of Joining" 
                    type="date"
                    variant="bordered" 
                    value={formData.date_of_joining} 
                    onChange={(e) => setFormData({...formData, date_of_joining: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Select 
                    label="Status" 
                    variant="bordered" 
                    selectedKeys={[formData.status]} 
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    isDisabled={modalMode === 'view'}
                  >
                    <SelectItem key="Active" value="Active">Active</SelectItem>
                    <SelectItem key="Suspended" value="Suspended">Suspended</SelectItem>
                    <SelectItem key="Terminated" value="Terminated">Terminated</SelectItem>
                  </Select>
                  <Input 
                    label="Avatar URL" 
                    variant="bordered"
                    placeholder="https://..."
                    value={formData.avatar_url || ''} 
                    onChange={(e) => setFormData({...formData, avatar_url: e.target.value})}
                    isReadOnly={modalMode === 'view'}
                  />
                  <Select
                    label="Employee Type"
                    variant="bordered"
                    selectedKeys={formData.employee_type ? [String(formData.employee_type)] : []}
                    onChange={(e) => setFormData({...formData, employee_type: e.target.value})}
                    isDisabled={modalMode === 'view'}
                    isRequired
                  >
                    {employeeTypes.map((t: any) => (
                      <SelectItem key={String(t.id)} value={String(t.id)}>{t.name}</SelectItem>
                    ))}
                  </Select>
                  <Select
                    label="Branch"
                    variant="bordered"
                    selectedKeys={formData.branch ? [String(formData.branch)] : []}
                    onChange={(e) => setFormData({...formData, branch: e.target.value})}
                    isDisabled={modalMode === 'view'}
                  >
                    {branches.map((b: any) => (
                      <SelectItem key={String(b.id)} value={String(b.id)}>
                        {b.name} {(!b.latitude || !b.longitude) ? '(Missing office coordinates)' : ''}
                      </SelectItem>
                    ))}
                  </Select>
                  {modalMode === 'view' ? (
                    <Input
                      label="Reporting manager"
                      variant="bordered"
                      value={
                        selectedEmployee?.reporting_manager_name ||
                        (tenantHasEmployees ? '—' : 'Root (no manager)')
                      }
                      isReadOnly
                      className="col-span-2"
                    />
                  ) : (
                    <Select
                      label="Reporting manager"
                      variant="bordered"
                      description={
                        tenantHasEmployees
                          ? 'Required for all employees except the first root executive'
                          : 'Optional for the first employee in the organization'
                      }
                      selectedKeys={
                        formData.reporting_manager ? [String(formData.reporting_manager)] : []
                      }
                      onChange={(e) =>
                        setFormData({ ...formData, reporting_manager: e.target.value })
                      }
                      isRequired={tenantHasEmployees}
                      className="col-span-2"
                    >
                      {managerOptions.map((emp: {
                        id: string;
                        first_name: string;
                        last_name: string;
                        employee_code: string;
                        designation_name?: string;
                      }) => (
                        <SelectItem key={String(emp.id)} value={String(emp.id)}>
                          {managerLabel(emp)}
                        </SelectItem>
                      ))}
                    </Select>
                  )}
                </div>
                {saveError && (
                  <p className="text-sm text-danger mt-2">{saveError}</p>
                )}
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
                    isDisabled={
                      !formData.employee_type ||
                      (tenantHasEmployees && !formData.reporting_manager && modalMode === 'create')
                    }
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
                    You are about to permanently delete employee <strong className="text-foreground">{itemToDelete?.first_name} {itemToDelete?.last_name}</strong>. 
                    This action cannot be undone and will revoke all of their platform access immediately.
                  </p>
                  
                  {/* Interactive Tip */}
                  <div className="bg-warning/10 border border-warning/20 rounded-xl p-4 mt-2 flex gap-3 items-start shadow-inner">
                    <span className="text-warning mt-0.5 text-lg">💡</span>
                    <p className="text-xs text-warning-600 dark:text-warning-500 font-medium leading-relaxed">
                      <strong>Pro Tip:</strong> Do not delete employees if they have resigned. Instead, edit their profile and set their Status to <strong>"Terminated"</strong> to retain their payroll and attendance history.
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
