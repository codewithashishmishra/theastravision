'use client';

import React, { useState } from 'react';
import { 
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, 
  Button, Input, DropdownTrigger, Dropdown, DropdownMenu, 
  DropdownItem, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, 
  useDisclosure, Switch, Accordion, AccordionItem, Chip, Divider
} from "@nextui-org/react";
import { Plus, Search, MoreVertical, Edit, Trash2, Shield, Settings2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { menuConfig } from '@/config/menuConfig';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

const ROLE_PRESETS = [
  'Company Admin', 'HR Admin', 'Payroll Admin', 
  'Finance Admin', 'IT Admin', 'Manager', 
  'Recruiter', 'Auditor', 'Operations Assistant', 'Custom Role'
];

export default function RolesAndPermissionsPage() {
  const queryClient = useQueryClient();
  const [filterValue, setFilterValue] = useState("");
  const {isOpen, onOpen, onOpenChange} = useDisclosure();
  
  // Form State
  const [roleName, setRoleName] = useState("Custom Role");
  const [roleDescription, setRoleDescription] = useState("");
  const [selectedPermissions, setSelectedPermissions] = useState<Set<string>>(new Set());

  // API Fetches
  const { data: dbPermissions = [] } = useQuery({
    queryKey: ['permissions'],
    queryFn: async () => {
      const res = await api.get('/permissions/');
      return res.data.results || [];
    }
  });

  const { data: roles = [], isLoading: isLoadingRoles } = useQuery({
    queryKey: ['roles'],
    queryFn: async () => {
      const res = await api.get('/roles/');
      return res.data.results || [];
    }
  });

  // Mutations
  const createRoleMutation = useMutation({
    mutationFn: async (newRole: any) => {
      return api.post('/roles/', newRole);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      onOpenChange(); // Close modal
    }
  });

  const allPermissionKeys = React.useMemo(() => {
    const keys = new Set<string>();
    menuConfig.forEach(section => {
      section.items.forEach(item => {
        keys.add(item.key);
        if (item.children) {
          item.children.forEach(child => keys.add(child.key));
        }
      });
    });
    return Array.from(keys);
  }, []);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedPermissions(new Set(allPermissionKeys));
    } else {
      setSelectedPermissions(new Set());
    }
  };

  const isAllSelected = selectedPermissions.size === allPermissionKeys.length && allPermissionKeys.length > 0;

  const handleTogglePermission = (key: string, checked: boolean, childKeys: string[] = []) => {
    const newPerms = new Set(selectedPermissions);
    
    if (checked) {
      newPerms.add(key);
      childKeys.forEach(k => newPerms.add(k)); // auto-check children
    } else {
      newPerms.delete(key);
      childKeys.forEach(k => newPerms.delete(k)); // auto-uncheck children
    }
    
    setSelectedPermissions(newPerms);
  };

  const handleSaveRole = () => {
    // Map selected string keys to database permission IDs
    const permissionIds = Array.from(selectedPermissions).map(key => {
      const dbPerm = dbPermissions.find((p: any) => p.code === key);
      return dbPerm ? dbPerm.id : null;
    }).filter(id => id !== null);

    createRoleMutation.mutate({
      name: roleName,
      description: roleDescription,
      permission_ids: permissionIds
    });
  };

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            <Shield className="text-primary" size={28} />
            Roles & Permissions Builder
          </h1>
          <p className="text-sm text-default-500 mt-1">
            Create custom roles and granularly define which menus and modules they can access.
          </p>
        </div>
        <Button 
          color="primary" 
          endContent={<Plus size={18} />} 
          className="font-bold shadow-lg shadow-primary/30" 
          onPress={() => {
            setRoleName("");
            setRoleDescription("");
            setSelectedPermissions(new Set());
            onOpen();
          }}
        >
          Create Custom Role
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
            placeholder="Search roles..."
            startContent={<Search className="text-default-300" size={18} />}
            value={filterValue}
            onClear={() => setFilterValue("")}
            onValueChange={setFilterValue}
            variant="faded"
            radius="lg"
          />
        </div>

        <Table 
          aria-label="Custom Roles Table" 
          shadow="none"
          classNames={{
            wrapper: "p-0 border-none bg-transparent",
            th: "bg-default-100/80 backdrop-blur-md text-default-700 font-extrabold tracking-wider z-10 py-4 uppercase text-xs",
            td: "py-4 border-b border-default-100 font-medium"
          }}
        >
          <TableHeader>
            <TableColumn>ROLE NAME</TableColumn>
            <TableColumn>DESCRIPTION</TableColumn>
            <TableColumn>ASSIGNED USERS</TableColumn>
            <TableColumn align="center">ACTIONS</TableColumn>
          </TableHeader>
          <TableBody 
            items={roles.filter((r: any) => r.name.toLowerCase().includes(filterValue.toLowerCase()))}
            isLoading={isLoadingRoles}
            emptyContent="No custom roles found."
          >
            {(item: any) => (
              <TableRow key={item.id}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                      <Settings2 size={16} />
                    </div>
                    <span className="font-bold">{item.name}</span>
                  </div>
                </TableCell>
                <TableCell className="text-default-500 max-w-md truncate">{item.description || 'No description'}</TableCell>
                <TableCell>
                  <Chip size="sm" variant="flat" color="secondary">{item.permissions?.length || 0} Permissions</Chip>
                </TableCell>
                <TableCell>
                  <div className="flex justify-end gap-2">
                    <Button isIconOnly size="sm" variant="light" color="primary">
                      <Edit size={18} />
                    </Button>
                    <Button isIconOnly size="sm" variant="light" color="danger">
                      <Trash2 size={18} />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </motion.div>

      {/* Role Builder Modal */}
      <Modal isOpen={isOpen} onOpenChange={onOpenChange} size="4xl" scrollBehavior="inside" backdrop="blur">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1 border-b border-divider pb-4">
                <h2 className="text-xl font-extrabold">Permission Matrix Builder</h2>
                <p className="text-sm text-default-500 font-normal">Define exactly which menus and sub-menus this role can view and manage.</p>
              </ModalHeader>
              <ModalBody className="py-6 bg-default-50/50">
                
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {/* Select Dropdown as requested */}
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium">Role Name <span className="text-danger">*</span></label>
                    <select 
                      className="bg-default-100 hover:bg-default-200 focus:bg-default-100 border-none outline-none rounded-xl h-14 px-4 text-sm font-medium transition-colors cursor-pointer"
                      value={roleName}
                      onChange={(e) => setRoleName(e.target.value)}
                    >
                      {ROLE_PRESETS.map(preset => (
                        <option key={preset} value={preset}>{preset}</option>
                      ))}
                    </select>
                  </div>
                  
                  <Input 
                    label="Description (Optional)" 
                    placeholder="Briefly describe the purpose of this role..."
                    variant="bordered"
                    value={roleDescription}
                    onValueChange={setRoleDescription}
                  />
                </div>

                <div className="flex flex-col gap-4">
                  <div className="flex justify-between items-center bg-primary/10 border border-primary/20 p-4 rounded-2xl shadow-inner">
                    <div>
                      <h3 className="font-bold text-primary text-lg flex items-center gap-2">
                        <Shield size={20} />
                        Menu Visibility Access
                      </h3>
                      <p className="text-xs text-primary/80 mt-0.5">Toggle individual modules or grant full platform access.</p>
                    </div>
                    <Switch 
                      color="primary"
                      size="lg"
                      isSelected={isAllSelected}
                      onValueChange={handleSelectAll}
                      classNames={{
                        wrapper: "group-data-[selected=true]:bg-primary"
                      }}
                    >
                      <span className="text-sm font-bold ml-1 text-primary">Select All</span>
                    </Switch>
                  </div>
                  
                  <Accordion variant="splitted" selectionMode="multiple">
                    {menuConfig.map((section, idx) => {
                      // Skip Super Admin Operations as they shouldn't be grantable by Company Admins typically, 
                      // but we'll show them for completeness in the demo.
                      return (
                        <AccordionItem 
                          key={idx} 
                          aria-label={section.section} 
                          title={<span className="font-bold text-base">{section.section}</span>}
                          subtitle={<span className="text-xs text-default-500">{section.items.length} modules available</span>}
                          className="bg-background shadow-sm border border-divider/50"
                        >
                          <div className="flex flex-col gap-6 pb-4 px-2">
                            {section.items.map(menuItem => {
                              const childKeys = menuItem.children?.map(c => c.key) || [];
                              const isMenuChecked = selectedPermissions.has(menuItem.key);

                              return (
                                <div key={menuItem.key} className="flex flex-col gap-3">
                                  <div className="flex justify-between items-center bg-default-100/50 p-3 rounded-xl">
                                    <div className="flex items-center gap-3">
                                      {menuItem.icon && <menuItem.icon size={20} className="text-primary" />}
                                      <div>
                                        <p className="font-bold">{menuItem.label}</p>
                                        <p className="text-xs text-default-500">Main Menu Access</p>
                                      </div>
                                    </div>
                                    <Switch 
                                      size="sm" 
                                      color="primary"
                                      isSelected={isMenuChecked}
                                      onValueChange={(checked) => handleTogglePermission(menuItem.key, checked, childKeys)}
                                    />
                                  </div>

                                  {/* Sub-menus */}
                                  {menuItem.children && (
                                    <div className="grid grid-cols-2 gap-3 pl-8">
                                      {menuItem.children.map(child => (
                                        <div key={child.key} className="flex justify-between items-center p-2 border border-divider rounded-lg">
                                          <span className="text-sm font-medium">{child.label}</span>
                                          <Switch 
                                            size="sm" 
                                            color="secondary"
                                            isSelected={selectedPermissions.has(child.key)}
                                            onValueChange={(checked) => handleTogglePermission(child.key, checked)}
                                          />
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                  <Divider className="my-1" />
                                </div>
                              );
                            })}
                          </div>
                        </AccordionItem>
                      )
                    })}
                  </Accordion>
                </div>

              </ModalBody>
              <ModalFooter className="border-t border-divider pt-4">
                <Button color="danger" variant="light" onPress={onClose}>
                  Cancel
                </Button>
                <Button 
                  color="primary" 
                  className="font-bold shadow-lg shadow-primary/30" 
                  onPress={handleSaveRole}
                  isLoading={createRoleMutation.isPending}
                >
                  Create Role
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
