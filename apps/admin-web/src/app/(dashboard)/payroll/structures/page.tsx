'use client';

import React, { useState } from 'react';
import {
  Button, Card, CardBody, Input, Switch, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure,
} from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';

type Structure = {
  id: string;
  employee: string;
  employee_name?: string;
  ctc: string;
  effective_date: string;
  variable_pay_enabled: boolean | null;
  variable_pay_amount: string | null;
  variable_pay_pct: string | null;
  components: Record<string, unknown>;
};

export default function SalaryStructuresPage() {
  const isAuthReady = useAuthReady();
  const queryClient = useQueryClient();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [edit, setEdit] = useState<Structure | null>(null);
  const [varEnabled, setVarEnabled] = useState<boolean | null>(null);
  const [varAmount, setVarAmount] = useState('');
  const [varPct, setVarPct] = useState('');

  const { data: structures } = useQuery({
    queryKey: ['payroll-structures'],
    enabled: isAuthReady,
    queryFn: async () => unwrapList<Structure>((await api.get('/payroll/structures/')).data),
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!edit) return;
      await api.patch(`/payroll/structures/${edit.id}/`, {
        variable_pay_enabled: varEnabled,
        variable_pay_amount: varAmount ? Number(varAmount) : null,
        variable_pay_pct: varPct ? Number(varPct) : null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payroll-structures'] });
      onClose();
    },
  });

  const openEdit = (row: Structure) => {
    setEdit(row);
    setVarEnabled(row.variable_pay_enabled);
    setVarAmount(row.variable_pay_amount ?? '');
    setVarPct(row.variable_pay_pct ?? '');
    onOpen();
  };

  return (
    <>
      <Card className="border border-divider">
        <CardBody className="p-6">
          <h1 className="text-2xl font-extrabold mb-4">Salary Structures & Variable Pay</h1>
          <Table aria-label="Salary structures">
            <TableHeader>
              <TableColumn>Employee</TableColumn>
              <TableColumn>CTC</TableColumn>
              <TableColumn>Variable Pay</TableColumn>
              <TableColumn>Actions</TableColumn>
            </TableHeader>
            <TableBody emptyContent="No salary structures. Assign CTC from employee onboarding.">
              {(structures ?? []).map((s) => (
                <TableRow key={s.id}>
                  <TableCell>{s.employee_name ?? s.employee}</TableCell>
                  <TableCell>{s.ctc}</TableCell>
                  <TableCell>
                    {s.variable_pay_enabled === null ? 'Inherit' : s.variable_pay_enabled ? 'On' : 'Off'}
                    {s.variable_pay_amount ? ` — ${s.variable_pay_amount}/mo` : ''}
                  </TableCell>
                  <TableCell>
                    <Button size="sm" variant="flat" onPress={() => openEdit(s)}>Edit</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalContent>
          <ModalHeader>Variable pay — {edit?.employee_name}</ModalHeader>
          <ModalBody className="flex flex-col gap-3">
            <p className="text-sm text-default-500">Leave override unset to inherit company default.</p>
            <Switch
              isSelected={varEnabled === true}
              onValueChange={(v) => setVarEnabled(v ? true : varEnabled === true ? false : null)}
            >
              Enable variable pay for this employee
            </Switch>
            <Input label="Monthly variable amount" value={varAmount} onValueChange={setVarAmount} />
            <Input label="Variable % of monthly CTC (e.g. 0.15)" value={varPct} onValueChange={setVarPct} />
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={onClose}>Cancel</Button>
            <Button color="primary" onPress={() => saveMutation.mutate()} isLoading={saveMutation.isPending}>Save</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
