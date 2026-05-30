'use client';

import React, { useState } from 'react';
import {
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell,
  Button, Input, Chip, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure,
  Select, SelectItem, Spinner,
} from '@nextui-org/react';
import { Search, Edit2, CalendarDays, Plus } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { unwrapList } from '@/lib/hrmsApi';

type LeaveBalanceRow = {
  id: string;
  employee: string;
  employee_name?: string;
  leave_type: string;
  leave_type_name?: string;
  balance: number;
  year: number;
};

export default function LeaveBalancesPage() {
  const queryClient = useQueryClient();
  const [filterValue, setFilterValue] = useState('');
  const { isOpen: isEditOpen, onOpen: onEditOpen, onOpenChange: onEditOpenChange } = useDisclosure();
  const [selectedRow, setSelectedRow] = useState<LeaveBalanceRow | null>(null);
  const [newBalance, setNewBalance] = useState('0');

  const { data, isLoading } = useQuery({
    queryKey: ['leave_balances'],
    queryFn: async () => {
      const res = await api.get('/leave/balances/');
      return unwrapList<LeaveBalanceRow>(res.data);
    },
  });

  const balances = (data ?? []).filter((row) => {
    if (!filterValue) return true;
    const q = filterValue.toLowerCase();
    return (
      String(row.employee_name ?? '').toLowerCase().includes(q) ||
      String(row.leave_type_name ?? '').toLowerCase().includes(q)
    );
  });

  const updateMutation = useMutation({
    mutationFn: async (payload: { id: string; balance: number }) =>
      api.patch(`/leave/balances/${payload.id}/`, { balance: payload.balance }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leave_balances'] });
      onEditOpenChange();
    },
  });

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            <CalendarDays className="text-primary" size={28} />
            Leave Balances
          </h1>
          <p className="text-sm text-default-500 mt-1">
            View and adjust employee leave balances by type and year.
          </p>
        </div>
        <Button color="primary" className="font-bold shadow-lg" startContent={<Plus size={18} />} isDisabled>
          Assign Leave Policy
        </Button>
      </div>

      <div className="bg-content1 border border-divider rounded-3xl overflow-hidden p-6 shadow-sm w-full">
        <Input
          isClearable
          className="max-w-md mb-6"
          placeholder="Search employees or leave types..."
          startContent={<Search className="text-default-300" size={18} />}
          value={filterValue}
          onClear={() => setFilterValue('')}
          onValueChange={setFilterValue}
          variant="faded"
          radius="lg"
        />

        {isLoading ? (
          <div className="flex justify-center p-12"><Spinner /></div>
        ) : (
          <Table aria-label="Leave Balances" className="w-full" classNames={{ wrapper: 'w-full' }}>
            <TableHeader>
              <TableColumn>EMPLOYEE</TableColumn>
              <TableColumn>LEAVE TYPE</TableColumn>
              <TableColumn>YEAR</TableColumn>
              <TableColumn>BALANCE</TableColumn>
              <TableColumn align="end">ACTIONS</TableColumn>
            </TableHeader>
            <TableBody emptyContent="No leave balances found. Run seed_hrms or assign policies.">
              {balances.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-bold">{item.employee_name ?? item.employee}</TableCell>
                  <TableCell>{item.leave_type_name ?? item.leave_type}</TableCell>
                  <TableCell>{item.year}</TableCell>
                  <TableCell>
                    <Chip size="sm" variant="flat" color={item.balance > 0 ? 'success' : 'danger'}>
                      {item.balance} days
                    </Chip>
                  </TableCell>
                  <TableCell>
                    <Button
                      isIconOnly
                      size="sm"
                      variant="light"
                      color="primary"
                      onPress={() => {
                        setSelectedRow(item);
                        setNewBalance(String(item.balance));
                        onEditOpen();
                      }}
                    >
                      <Edit2 size={16} />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <Modal isOpen={isEditOpen} onOpenChange={onEditOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Adjust balance — {selectedRow?.employee_name}</ModalHeader>
              <ModalBody>
                <Input
                  type="number"
                  label="Balance (days)"
                  value={newBalance}
                  onValueChange={setNewBalance}
                  variant="bordered"
                />
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>Cancel</Button>
                <Button
                  color="primary"
                  isLoading={updateMutation.isPending}
                  onPress={() => {
                    if (selectedRow) {
                      updateMutation.mutate({ id: selectedRow.id, balance: parseFloat(newBalance) || 0 });
                    }
                  }}
                >
                  Save
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
