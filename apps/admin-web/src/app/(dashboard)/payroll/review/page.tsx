'use client';

import React from 'react';
import { Button, Card, CardBody } from '@nextui-org/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { payrollApi, unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';

type Run = { id: string; month: number; year: number; jurisdiction: string; status: string };

export default function PayrollReviewPage() {
  const isAuthReady = useAuthReady();
  const queryClient = useQueryClient();
  const { data: runs } = useQuery({
    queryKey: ['payroll-runs'],
    enabled: isAuthReady,
    queryFn: async () => unwrapList<Run>((await payrollApi.runs.list()).data),
  });

  const approve = useMutation({
    mutationFn: (id: string) => payrollApi.runs.approve(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payroll-runs'] }),
  });

  return (
    <Card className="border border-divider">
      <CardBody className="p-6 flex flex-col gap-3">
        <h1 className="text-xl font-bold">Review Payroll Runs</h1>
        {(runs ?? []).filter((r) => r.status === 'Processing').map((r) => (
          <div key={r.id} className="flex justify-between items-center border-b border-divider py-2">
            <span>{r.jurisdiction} — {r.month}/{r.year} ({r.status})</span>
            <Button size="sm" color="primary" onPress={() => approve.mutate(r.id)}>Approve</Button>
          </div>
        ))}
      </CardBody>
    </Card>
  );
}
