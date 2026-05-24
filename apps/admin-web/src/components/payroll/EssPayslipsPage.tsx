'use client';

import React from 'react';
import { Button, Card, CardBody, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { payrollApi, unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';

type Payslip = {
  id: string;
  gross_pay: string;
  total_deductions: string;
  net_pay: string;
  currency: string;
  month: number;
  year: number;
  is_released: boolean;
};

export function EssPayslipsPage() {
  const isAuthReady = useAuthReady();

  const { data: payslips } = useQuery({
    queryKey: ['ess-payslips'],
    enabled: isAuthReady,
    queryFn: async () => unwrapList<Payslip>((await payrollApi.payslips.list()).data),
  });

  const downloadPdf = async (id: string) => {
    const res = await payrollApi.payslips.pdf(id);
    const url = window.URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payslip_${id}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const released = (payslips ?? []).filter((p) => p.is_released);

  return (
    <Card className="border border-divider">
      <CardBody className="p-6">
        <h1 className="text-2xl font-extrabold mb-4">My Payslips</h1>
        <Table aria-label="Payslips">
          <TableHeader>
            <TableColumn>Period</TableColumn>
            <TableColumn>Gross</TableColumn>
            <TableColumn>Net</TableColumn>
            <TableColumn>PDF</TableColumn>
          </TableHeader>
          <TableBody emptyContent="No released payslips yet.">
            {released.map((p) => (
              <TableRow key={p.id}>
                <TableCell>{p.month}/{p.year}</TableCell>
                <TableCell>{p.currency} {p.gross_pay}</TableCell>
                <TableCell>{p.currency} {p.net_pay}</TableCell>
                <TableCell>
                  <Button size="sm" color="primary" variant="flat" onPress={() => downloadPdf(p.id)}>
                    Download
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardBody>
    </Card>
  );
}
