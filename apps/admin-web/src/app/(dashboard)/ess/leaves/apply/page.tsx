'use client';

import React, { useState } from 'react';
import { Card, CardBody, Button, Input, Textarea, Select, SelectItem } from '@nextui-org/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { leaveApi, unwrapList } from '@/lib/hrmsApi';

export default function ApplyLeavePage() {
  const [form, setForm] = useState({ leave_type_id: '', start_date: '', end_date: '', reason: '' });

  const { data: types } = useQuery({
    queryKey: ['leave-types'],
    queryFn: async () => {
      const res = await leaveApi.types.list();
      return unwrapList<{ id: string; name: string }>(res.data);
    },
  });

  const apply = useMutation({
    mutationFn: () => leaveApi.requests.apply(form),
  });

  return (
    <div className="max-w-xl mx-auto w-full flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Apply Leave</h1>
      <Card className="border border-divider">
        <CardBody className="gap-4">
          <Select label="Leave Type" onSelectionChange={(k) => setForm((f) => ({ ...f, leave_type_id: Array.from(k)[0] as string }))}>
            {(types ?? []).map((t) => <SelectItem key={t.id}>{t.name}</SelectItem>)}
          </Select>
          <Input type="date" label="Start" onValueChange={(v) => setForm((f) => ({ ...f, start_date: v }))} />
          <Input type="date" label="End" onValueChange={(v) => setForm((f) => ({ ...f, end_date: v }))} />
          <Textarea label="Reason" onValueChange={(v) => setForm((f) => ({ ...f, reason: v }))} />
          <Button color="primary" isLoading={apply.isPending} onPress={() => apply.mutate()}>
            Submit Application
          </Button>
          {apply.isSuccess && <p className="text-success text-sm">Leave submitted successfully.</p>}
        </CardBody>
      </Card>
    </div>
  );
}
