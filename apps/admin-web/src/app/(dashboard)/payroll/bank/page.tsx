'use client';

import React from 'react';
import { Button, Card, CardBody } from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { payrollApi, unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';

type Run = { id: string; month: number; year: number; jurisdiction: string; status: string };

export default function PayrollBankPage() {
  const isAuthReady = useAuthReady();
  const { data: runs } = useQuery({
    queryKey: ['payroll-runs'],
    enabled: isAuthReady,
    queryFn: async () => unwrapList<Run>((await payrollApi.runs.list()).data),
  });

  const download = async (id: string, jurisdiction: string, month: number, year: number) => {
    const res = await payrollApi.runs.bankExport(id);
    const url = window.URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bank_${jurisdiction}_${year}_${month}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Card className="border border-divider">
      <CardBody className="p-6 flex flex-col gap-3">
        <h1 className="text-xl font-bold">Bank Transfer CSV Export</h1>
        {(runs ?? []).filter((r) => ['Approved', 'Locked', 'Released'].includes(r.status)).map((r) => (
          <div key={r.id} className="flex justify-between items-center border-b border-divider py-2">
            <span>{r.jurisdiction} — {r.month}/{r.year}</span>
            <Button size="sm" onPress={() => download(r.id, r.jurisdiction, r.month, r.year)}>Download CSV</Button>
          </div>
        ))}
      </CardBody>
    </Card>
  );
}
