'use client';

import React from 'react';
import { Button, Card, CardBody, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { payrollApi, unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';

type Payslip = {
  id: string;
  gross_pay: string;
  net_pay: string;
  currency: string;
  month: number;
  year: number;
  is_released: boolean;
};

export function PayslipReleasePage() {
  const isAuthReady = useAuthReady();
  const { data: payslips } = useQuery({
    queryKey: ['payroll-payslips-admin'],
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

  return (
    <Card className="border border-divider">
      <CardBody className="p-6">
        <h1 className="text-2xl font-extrabold mb-4">Payslip Release & Download</h1>
        <Table aria-label="Payslips">
          <TableHeader>
            <TableColumn>Period</TableColumn>
            <TableColumn>Net</TableColumn>
            <TableColumn>Released</TableColumn>
            <TableColumn>PDF</TableColumn>
          </TableHeader>
          <TableBody emptyContent="No payslips. Run payroll first.">
            {(payslips ?? []).map((p) => (
              <TableRow key={p.id}>
                <TableCell>{p.month}/{p.year}</TableCell>
                <TableCell>{p.currency} {p.net_pay}</TableCell>
                <TableCell>{p.is_released ? 'Yes' : 'No'}</TableCell>
                <TableCell>
                  <Button size="sm" variant="flat" onPress={() => downloadPdf(p.id)}>PDF</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardBody>
    </Card>
  );
}
