'use client';

import React, { useState } from 'react';
import {
  Button, Card, CardBody, Progress, Select, SelectItem, Input, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Chip,
} from '@nextui-org/react';
import { Calculator, CheckCircle2 } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { payrollApi, unwrapList } from '@/lib/hrmsApi';
import { getStoredJurisdictions } from '@/lib/jurisdiction';

type PayrollRun = { id: string; month: number; year: number; jurisdiction: string; status: string };
type Payslip = { id: string; gross_pay: string; total_deductions: string; net_pay: string; currency: string; employee: string };

export default function PayrollGeneratePage() {
  const queryClient = useQueryClient();
  const jurisdictions = getStoredJurisdictions();
  const [step, setStep] = useState(1);
  const [jurisdiction, setJurisdiction] = useState(jurisdictions[0] ?? 'IN');
  const [month, setMonth] = useState(String(new Date().getMonth() + 1));
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [runId, setRunId] = useState<string | null>(null);

  const { data: payslips } = useQuery({
    queryKey: ['payroll-payslips', runId],
    enabled: !!runId && step === 3,
    queryFn: async () => unwrapList<Payslip>((await payrollApi.payslips.list()).data),
  });

  const createRunMutation = useMutation({
    mutationFn: async () => {
      const res = await payrollApi.runs.create({
        month: Number(month),
        year: Number(year),
        jurisdiction,
        status: 'Draft',
      });
      return res.data as PayrollRun;
    },
    onSuccess: (run) => {
      setRunId(run.id);
      generateMutation.mutate(run.id);
    },
  });

  const generateMutation = useMutation({
    mutationFn: async (id: string) => payrollApi.runs.generate(id),
    onSuccess: (_, id) => {
      setStep(3);
      queryClient.invalidateQueries({ queryKey: ['payroll-payslips', id] });
    },
  });

  const handleStart = () => {
    setStep(2);
    createRunMutation.mutate();
  };

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            <Calculator className="text-primary" size={28} />
            Run Payroll Engine
          </h1>
          <p className="text-sm text-default-500 mt-1">Jurisdiction-specific statutory payroll calculation.</p>
        </div>
      </div>

      {step === 1 && (
        <Card className="w-full max-w-2xl mx-auto border border-divider mt-6">
          <CardBody className="p-8 flex flex-col gap-4">
            <Select label="Payroll Jurisdiction" selectedKeys={[jurisdiction]} onSelectionChange={(k) => setJurisdiction(String(Array.from(k)[0]))}>
              {jurisdictions.map((j) => <SelectItem key={j}>{j}</SelectItem>)}
            </Select>
            <div className="flex gap-4">
              <Input label="Month" value={month} onValueChange={setMonth} />
              <Input label="Year" value={year} onValueChange={setYear} />
            </div>
            <Button color="primary" size="lg" className="font-bold" onPress={handleStart}>
              Start Payroll Run
            </Button>
          </CardBody>
        </Card>
      )}

      {step === 2 && (
        <Card className="w-full max-w-2xl mx-auto border border-divider mt-6">
          <CardBody className="p-10 text-center flex flex-col items-center">
            <Calculator size={48} className="text-primary animate-bounce mb-6" />
            <h2 className="text-2xl font-extrabold mb-4">Calculating {jurisdiction} payroll...</h2>
            <Progress size="md" isIndeterminate color="primary" className="max-w-md" />
          </CardBody>
        </Card>
      )}

      {step === 3 && (
        <div className="flex flex-col gap-4">
          <div className="bg-success/10 border border-success/20 p-4 rounded-2xl flex items-center gap-3 text-success-700 font-bold">
            <CheckCircle2 size={24} />
            Payroll run complete — {jurisdiction} {month}/{year}
          </div>
          <Table aria-label="Payslips">
            <TableHeader>
              <TableColumn>GROSS</TableColumn>
              <TableColumn>DEDUCTIONS</TableColumn>
              <TableColumn>NET</TableColumn>
              <TableColumn>STATUS</TableColumn>
            </TableHeader>
            <TableBody emptyContent="No payslips generated">
              {(payslips ?? []).map((p) => (
                <TableRow key={p.id}>
                  <TableCell>{p.currency} {p.gross_pay}</TableCell>
                  <TableCell>{p.currency} {p.total_deductions}</TableCell>
                  <TableCell>{p.currency} {p.net_pay}</TableCell>
                  <TableCell><Chip size="sm" color="success">Calculated</Chip></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
