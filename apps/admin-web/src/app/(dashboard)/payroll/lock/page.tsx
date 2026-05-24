'use client';

import React from 'react';
import { Button, Card, CardBody } from '@nextui-org/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { payrollApi, unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';

type Run = { id: string; month: number; year: number; jurisdiction: string; status: string };

export default function PayrollLockPage() {
  const isAuthReady = useAuthReady();
  const queryClient = useQueryClient();
  const { data: runs } = useQuery({
    queryKey: ['payroll-runs'],
    enabled: isAuthReady,
    queryFn: async () => unwrapList<Run>((await payrollApi.runs.list()).data),
  });

  const lock = useMutation({
    mutationFn: (id: string) => payrollApi.runs.lock(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payroll-runs'] }),
  });
  const release = useMutation({
    mutationFn: (id: string) => payrollApi.runs.release(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payroll-runs'] }),
  });

  return (
    <Card className="border border-divider">
      <CardBody className="p-6 flex flex-col gap-3">
        <h1 className="text-xl font-bold">Lock & Release Payroll</h1>
        {(runs ?? []).map((r) => (
          <div key={r.id} className="flex justify-between items-center border-b border-divider py-2 gap-2">
            <span>{r.jurisdiction} — {r.month}/{r.year} ({r.status})</span>
            <div className="flex gap-2">
              {r.status === 'Approved' && <Button size="sm" onPress={() => lock.mutate(r.id)}>Lock</Button>}
              {r.status === 'Locked' && <Button size="sm" color="success" onPress={() => release.mutate(r.id)}>Release Payslips</Button>}
            </div>
          </div>
        ))}
      </CardBody>
    </Card>
  );
}
