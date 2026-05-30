'use client';

import React, { useState } from 'react';
import {
  Card, CardBody, Button, Input, Select, SelectItem, Textarea, Chip,
  Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure,
} from '@nextui-org/react';
import { Receipt, UploadCloud, Banknote, ShieldCheck } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { unwrapList } from '@/lib/hrmsApi';
import { validateDateNotFuture, validateNumber, validateRequired } from '@/lib/validation';

type ExpenseClaim = {
  id: string;
  amount: number;
  description?: string;
  status: string;
  expense_date?: string;
  category?: string;
};

export default function ExpenseClaimsPage() {
  const queryClient = useQueryClient();
  const successModal = useDisclosure();
  const [category, setCategory] = useState('');
  const [amount, setAmount] = useState('');
  const [expenseDate, setExpenseDate] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const { data: claims = [] } = useQuery({
    queryKey: ['my-expense-claims'],
    queryFn: async () => {
      const res = await api.get('/expenses/claims/');
      return unwrapList<ExpenseClaim>(res.data);
    },
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      const catErr = validateRequired(category, 'Category');
      const amtErr = validateNumber(amount, { min: 0.01, label: 'Amount' });
      const dateErr = validateDateNotFuture(expenseDate, 'Date of expense');
      const first = catErr || amtErr || dateErr;
      if (first) throw new Error(first);
      const today = new Date().toISOString().slice(0, 10);
      return api.post('/expenses/claims/', {
        amount: parseFloat(amount) || 0,
        description: description || category,
        expense_date: expenseDate || today,
        category,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-expense-claims'] });
      setCategory('');
      setAmount('');
      setExpenseDate('');
      setDescription('');
      setError('');
      successModal.onOpen();
    },
    onError: (err: unknown) => {
      setError(err instanceof Error ? err.message : 'Failed to submit claim.');
    },
  });

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground">My Expense Claims</h1>
          <p className="text-sm text-default-500 mt-1">Submit receipts for business travel and reimbursements.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-8 flex flex-col gap-6">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <Banknote className="text-success" /> New Claim Request
            </h2>

            <Select
              label="Expense Category"
              variant="bordered"
              selectedKeys={category ? [category] : []}
              onSelectionChange={(keys) => setCategory(String(Array.from(keys)[0] ?? ''))}
            >
              <SelectItem key="travel">Travel</SelectItem>
              <SelectItem key="hotel">Accommodation</SelectItem>
              <SelectItem key="meals">Meals</SelectItem>
              <SelectItem key="internet">Internet</SelectItem>
              <SelectItem key="office">Office Supplies</SelectItem>
            </Select>

            <div className="flex gap-4">
              <Input
                type="number"
                label="Amount"
                placeholder="0.00"
                variant="bordered"
                className="flex-1"
                value={amount}
                onValueChange={setAmount}
              />
              <Input
                type="date"
                label="Date of Expense"
                variant="bordered"
                className="flex-1"
                value={expenseDate}
                max={new Date().toISOString().slice(0, 10)}
                onValueChange={setExpenseDate}
              />
            </div>

            <Textarea
              label="Business Justification"
              variant="bordered"
              minRows={2}
              value={description}
              onValueChange={setDescription}
            />

            <div className="border-2 border-dashed border-divider rounded-xl p-8 text-center">
              <UploadCloud size={24} className="mx-auto text-primary mb-2" />
              <p className="text-sm font-bold">Receipt upload (coming soon)</p>
            </div>

            {error && <p className="text-sm text-danger">{error}</p>}

            <Button
              color="primary"
              size="lg"
              className="font-bold"
              isLoading={submitMutation.isPending}
              onPress={() => submitMutation.mutate()}
            >
              Submit for Approval
            </Button>
          </CardBody>
        </Card>

        <div className="flex flex-col gap-4 w-full">
          <h3 className="font-bold text-lg">Claim History</h3>
          {claims.length === 0 ? (
            <p className="text-default-500 text-sm">No claims yet.</p>
          ) : (
            claims.map((exp) => (
              <Card key={exp.id} className="shadow-sm border border-divider w-full">
                <CardBody className="p-5 flex flex-row items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Receipt className="text-default-600" size={20} />
                    <div>
                      <span className="font-bold">{exp.description ?? exp.category ?? 'Expense'}</span>
                      <p className="text-xs text-default-500">{exp.expense_date ?? '—'}</p>
                    </div>
                  </div>
                  <div className="text-end">
                    <span className="font-bold">{exp.amount}</span>
                    <Chip size="sm" variant="flat" className="ml-2">{exp.status}</Chip>
                  </div>
                </CardBody>
              </Card>
            ))
          )}
        </div>
      </div>

      <Modal isOpen={successModal.isOpen} onOpenChange={successModal.onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Claim submitted</ModalHeader>
              <ModalBody>
                <p>Your expense claim is pending Finance approval.</p>
              </ModalBody>
              <ModalFooter>
                <Button color="primary" onPress={onClose}>OK</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
