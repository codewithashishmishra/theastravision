'use client';

import React, { useState } from 'react';
import {
  Button, Card, CardBody, Tabs, Tab, Select, SelectItem, Input, Chip,
} from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { getStoredJurisdictions, type Jurisdiction } from '@/lib/jurisdiction';
import { unwrapList } from '@/lib/hrmsApi';
import { useAuthReady } from '@/lib/AuthProvider';

type DocRow = {
  id: string;
  document_type: string;
  fiscal_year: number;
  jurisdiction: string;
  generated_at: string;
};

export function ComplianceHubPage({ title }: { title: string }) {
  const jurisdictions = getStoredJurisdictions();
  const isAuthReady = useAuthReady();
  const queryClient = useQueryClient();
  const [fy, setFy] = useState('2025');
  const [month, setMonth] = useState('5');
  const [quarter, setQuarter] = useState('1');
  const [message, setMessage] = useState<string | null>(null);

  const { data: docs } = useQuery({
    queryKey: ['compliance-documents'],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await api.get('/compliance/documents/');
      return unwrapList<DocRow>(res.data);
    },
  });

  const actionMutation = useMutation({
    mutationFn: async (payload: { url: string; body?: Record<string, unknown> }) => {
      const res = await api.post(payload.url, payload.body ?? {});
      return res.data;
    },
    onSuccess: (data) => {
      setMessage(`Success: ${JSON.stringify(data)}`);
      queryClient.invalidateQueries({ queryKey: ['compliance-documents'] });
    },
    onError: (err: Error) => setMessage(err.message),
  });

  const exportMutation = useMutation({
    mutationFn: async (payload: { url: string; body: Record<string, unknown>; filename: string }) => {
      const res = await api.post(payload.url, payload.body, { responseType: 'blob' });
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = payload.filename;
      a.click();
      window.URL.revokeObjectURL(url);
    },
    onSuccess: () => setMessage('Export downloaded.'),
    onError: (err: Error) => setMessage(err.message),
  });

  const tabs: { key: Jurisdiction; title: string; content: React.ReactNode }[] = [];
  if (jurisdictions.includes('IN')) {
    tabs.push({
      key: 'IN',
      title: 'India',
      content: (
        <div className="flex flex-wrap gap-3 items-end">
          <Input label="Financial Year" value={fy} onValueChange={setFy} className="max-w-xs" />
          <Input label="Month (ECR)" value={month} onValueChange={setMonth} className="max-w-xs" />
          <Button color="primary" onPress={() => actionMutation.mutate({ url: '/compliance/actions/form16/generate/', body: { fy: Number(fy) } })}>
            Generate Form 16
          </Button>
          <Button variant="flat" onPress={() => actionMutation.mutate({ url: '/compliance/actions/form12ba/generate/', body: { fy: Number(fy) } })}>
            Generate Form 12BA
          </Button>
          <Button variant="flat" onPress={() => exportMutation.mutate({ url: '/compliance/actions/ecr/export/', body: { month: Number(month), year: Number(fy) }, filename: `ecr_${fy}_${month}.csv` })}>
            Export ECR CSV
          </Button>
        </div>
      ),
    });
  }
  if (jurisdictions.includes('US')) {
    tabs.push({
      key: 'US',
      title: 'United States',
      content: (
        <div className="flex flex-wrap gap-3 items-end">
          <Input label="Tax Year" value={fy} onValueChange={setFy} className="max-w-xs" />
          <Select label="Quarter" selectedKeys={[quarter]} onSelectionChange={(k) => setQuarter(String(Array.from(k)[0]))} className="max-w-xs">
            <SelectItem key="1">Q1</SelectItem>
            <SelectItem key="2">Q2</SelectItem>
            <SelectItem key="3">Q3</SelectItem>
            <SelectItem key="4">Q4</SelectItem>
          </Select>
          <Button color="primary" onPress={() => actionMutation.mutate({ url: '/compliance/actions/w2/generate/', body: { tax_year: Number(fy) } })}>
            Generate W-2
          </Button>
          <Button variant="flat" onPress={() => actionMutation.mutate({ url: '/compliance/actions/1095c/generate/', body: { tax_year: Number(fy) } })}>
            Generate 1095-C
          </Button>
          <Button variant="flat" onPress={() => exportMutation.mutate({ url: '/compliance/actions/941/export/', body: { quarter: Number(quarter), year: Number(fy) }, filename: `941_q${quarter}_${fy}.csv` })}>
            Export Form 941 CSV
          </Button>
        </div>
      ),
    });
  }
  if (jurisdictions.includes('CA')) {
    tabs.push({
      key: 'CA',
      title: 'Canada',
      content: (
        <div className="flex flex-wrap gap-3 items-end">
          <Input label="Tax Year" value={fy} onValueChange={setFy} className="max-w-xs" />
          <Button color="primary" onPress={() => actionMutation.mutate({ url: '/compliance/actions/t4/generate/', body: { tax_year: Number(fy) } })}>
            Generate T4
          </Button>
          <Button variant="flat" onPress={() => actionMutation.mutate({ url: '/compliance/actions/rl1/generate/', body: { tax_year: Number(fy) } })}>
            Generate RL-1 (Quebec)
          </Button>
        </div>
      ),
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <Card className="border border-divider shadow-sm">
        <CardBody className="p-6">
          <h1 className="text-2xl font-extrabold">{title}</h1>
          <p className="text-sm text-default-500 mt-1">Jurisdiction-aware statutory reports and filing exports.</p>
        </CardBody>
      </Card>
      {message && <Chip color="primary" variant="flat">{message}</Chip>}
      <Button
        color="secondary"
        variant="flat"
        className="self-start"
        onPress={() => actionMutation.mutate({ url: '/compliance/actions/bulk-year-end/', body: { fy: Number(fy) } })}
      >
        Queue bulk year-end (all jurisdictions)
      </Button>
      <Tabs aria-label="Compliance jurisdictions">
        {tabs.map((t) => (
          <Tab key={t.key} title={t.title}>{t.content}</Tab>
        ))}
      </Tabs>
      <Card className="border border-divider">
        <CardBody className="p-4">
          <h2 className="font-bold mb-3">Generated Documents</h2>
          <div className="flex flex-col gap-2 text-sm">
            {(docs ?? []).map((d) => (
              <div key={d.id} className="flex justify-between border-b border-divider py-2">
                <span>{d.document_type} — FY {d.fiscal_year} ({d.jurisdiction})</span>
                <span className="text-default-400">{new Date(d.generated_at).toLocaleString()}</span>
              </div>
            ))}
            {(docs ?? []).length === 0 && <p className="text-default-400">No documents generated yet.</p>}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
