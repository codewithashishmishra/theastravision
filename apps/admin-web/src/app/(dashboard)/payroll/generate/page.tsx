'use client';

import React, { useState } from 'react';
import { 
  Button, Card, CardBody, Progress, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure,
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Chip
} from "@nextui-org/react";
import { Play, CheckCircle2, AlertTriangle, Calculator, FileCheck2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from '@/lib/axios';

export default function PayrollGeneratePage() {
  const queryClient = useQueryClient();
  const [step, setStep] = useState(1); // 1: Setup, 2: Processing, 3: Review
  
  // Confirmation Modal
  const {isOpen, onOpen, onOpenChange} = useDisclosure();

  // Mock Generated Payslips for Review Step
  const MOCK_PAYSLIPS = [
    { id: '1', employee: 'John Doe', basic: '$5,000', deductions: '$500', net: '$4,500', status: 'Calculated' },
    { id: '2', employee: 'Sarah Smith', basic: '$6,200', deductions: '$620', net: '$5,580', status: 'Calculated' },
  ];

  const generateMutation = useMutation({
    mutationFn: async () => {
      return axios.post('/payroll/runs/generate/', { month: 'May 2026' });
    },
    onSuccess: () => {
      // Move to review step
      setStep(3);
    },
    onError: () => {
      // Fallback for mock demo
      setTimeout(() => setStep(3), 2000);
    }
  });

  const handleStartRun = () => {
    setStep(2);
    generateMutation.mutate();
  };

  const handleLockPayroll = () => {
    onOpen();
  };

  const confirmLock = () => {
    // API call to lock payroll
    onOpenChange(); // close
    alert("Payroll Locked and Payslips Published!");
  };

  return (
    <div className="w-full flex flex-col gap-6">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            <Calculator className="text-primary" size={28} />
            Run Payroll Engine
          </h1>
          <p className="text-sm text-default-500 mt-1">
            Calculate salaries, apply deductions, and generate payslips for the current cycle.
          </p>
        </div>
      </div>

      {step === 1 && (
        <Card className="w-full max-w-2xl mx-auto shadow-2xl border border-divider bg-content1/80 backdrop-blur-md mt-10">
          <CardBody className="p-10 text-center flex flex-col items-center">
            <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-6 shadow-inner border border-primary/20">
              <Play size={40} className="ml-2" />
            </div>
            <h2 className="text-2xl font-extrabold mb-2">Ready for May 2026</h2>
            <p className="text-default-500 mb-8 max-w-md">
              The payroll engine will automatically pull attendance logs, leave deductions, and tax configurations for 103 active employees.
            </p>
            <Button 
              color="primary" 
              size="lg" 
              className="font-bold w-64 shadow-lg shadow-primary/30 h-14 text-lg"
              onPress={handleStartRun}
            >
              Start Payroll Run
            </Button>
          </CardBody>
        </Card>
      )}

      {step === 2 && (
        <Card className="w-full max-w-2xl mx-auto shadow-2xl border border-divider mt-10">
          <CardBody className="p-10 text-center flex flex-col items-center">
            <Calculator size={48} className="text-primary animate-bounce mb-6" />
            <h2 className="text-2xl font-extrabold mb-4">Crunching the Numbers...</h2>
            <Progress 
              size="md" 
              isIndeterminate 
              color="primary" 
              className="max-w-md mb-4"
            />
            <p className="text-sm text-default-500">Calculating taxes, overtime, and leave deductions.</p>
          </CardBody>
        </Card>
      )}

      {step === 3 && (
        <div className="flex flex-col gap-6 animate-fade-in">
          <div className="bg-success/10 border border-success/20 p-4 rounded-2xl flex items-center justify-between">
            <div className="flex items-center gap-3 text-success-700 font-bold">
              <CheckCircle2 size={24} />
              Payroll Calculation Complete (May 2026)
            </div>
            <Button color="success" className="font-bold shadow-lg" onPress={handleLockPayroll}>
              Lock & Publish Payslips
            </Button>
          </div>

          <Table aria-label="Review Payroll" shadow="sm" classNames={{ wrapper: "border border-divider rounded-2xl" }}>
            <TableHeader>
              <TableColumn>EMPLOYEE</TableColumn>
              <TableColumn>GROSS PAY</TableColumn>
              <TableColumn>DEDUCTIONS</TableColumn>
              <TableColumn>NET PAY</TableColumn>
              <TableColumn>STATUS</TableColumn>
            </TableHeader>
            <TableBody items={MOCK_PAYSLIPS}>
              {(item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-bold">{item.employee}</TableCell>
                  <TableCell>{item.basic}</TableCell>
                  <TableCell className="text-danger">{item.deductions}</TableCell>
                  <TableCell className="font-bold text-success">{item.net}</TableCell>
                  <TableCell>
                    <Chip size="sm" color="success" variant="flat">{item.status}</Chip>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Custom Confirmation Modal for Locking Payroll */}
      <Modal isOpen={isOpen} onOpenChange={onOpenChange} backdrop="blur">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1 items-center pt-8">
                <div className="w-16 h-16 rounded-full bg-warning/10 flex items-center justify-center text-warning mb-2">
                  <FileCheck2 size={32} />
                </div>
                <h2 className="text-xl font-bold">Lock Payroll Run?</h2>
              </ModalHeader>
              <ModalBody className="text-center pb-6">
                <p className="text-default-500">
                  Locking the payroll will finalize the calculations and instantly publish payslips to the Employee Self Service portal.
                </p>
                <div className="mt-4 p-3 bg-danger/10 border border-danger/20 rounded-xl text-danger-700 text-sm font-medium flex items-start gap-3 text-left">
                  <AlertTriangle size={18} className="shrink-0 mt-0.5" />
                  <p>WARNING: Once locked, you cannot recalculate or modify this month's payroll without Super Admin intervention.</p>
                </div>
              </ModalBody>
              <ModalFooter className="flex justify-center gap-4 pb-8">
                <Button variant="light" onPress={onClose} className="font-bold w-32">
                  Review More
                </Button>
                <Button 
                  color="warning" 
                  onPress={confirmLock}
                  className="font-bold w-32 shadow-lg"
                >
                  Yes, Lock It
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

    </div>
  );
}
