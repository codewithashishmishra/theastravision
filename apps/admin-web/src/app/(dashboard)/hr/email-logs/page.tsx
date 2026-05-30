'use client';

import React, { useMemo, useState } from 'react';
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  Button,
  Select,
  SelectItem,
  Input,
  Spinner,
} from '@nextui-org/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { outboundEmailApi } from '@/lib/hrmsApi';
import { unwrapList } from '@/lib/hrmsApi';

type EmailLog = {
  id: string;
  from_email: string;
  from_name: string;
  to_emails: string[];
  subject: string;
  status: string;
  source: string;
  sent_at: string | null;
  opened_at: string | null;
  smtp_error: string;
  created_at: string;
};

const STATUS_COLOR: Record<string, 'success' | 'danger' | 'warning' | 'default' | 'primary'> = {
  sent: 'success',
  failed: 'danger',
  queued: 'warning',
  opened: 'primary',
};

export default function EmailLogsPage() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('');
  const [source, setSource] = useState('');
  const [search, setSearch] = useState('');

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (status) p.status = status;
    if (source) p.source = source;
    if (search.trim()) p.search = search.trim();
    return p;
  }, [status, source, search]);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['outbound-email-logs', params],
    queryFn: async () => {
      const res = await outboundEmailApi.list(params);
      return unwrapList<EmailLog>(res.data);
    },
  });

  const resend = useMutation({
    mutationFn: (id: string) => outboundEmailApi.resend(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['outbound-email-logs'] });
    },
  });

  const renotify = useMutation({
    mutationFn: (id: string) => outboundEmailApi.notify(id),
  });

  const logs = data ?? [];

  return (
    <div className="w-full flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-extrabold text-foreground">Email Logs</h1>
        <p className="text-default-500 mt-1">
          Outbound email history for your organization. Resend failed messages or re-notify admins.
        </p>
      </div>

      <div className="flex flex-wrap gap-3 items-end">
        <Select
          label="Status"
          className="max-w-[160px]"
          selectedKeys={status ? [status] : []}
          onSelectionChange={(keys) => setStatus(Array.from(keys)[0]?.toString() || '')}
        >
          <SelectItem key="">All</SelectItem>
          <SelectItem key="sent">Sent</SelectItem>
          <SelectItem key="failed">Failed</SelectItem>
          <SelectItem key="opened">Opened</SelectItem>
          <SelectItem key="queued">Queued</SelectItem>
        </Select>
        <Select
          label="Source"
          className="max-w-[200px]"
          selectedKeys={source ? [source] : []}
          onSelectionChange={(keys) => setSource(Array.from(keys)[0]?.toString() || '')}
        >
          <SelectItem key="">All</SelectItem>
          <SelectItem key="recruitment_outreach">Recruitment</SelectItem>
          <SelectItem key="interview_invite">Interview invite</SelectItem>
          <SelectItem key="cold_campaign">Cold campaign</SelectItem>
          <SelectItem key="test">Test</SelectItem>
          <SelectItem key="manual_resend">Resend</SelectItem>
        </Select>
        <Input
          label="Search"
          className="max-w-xs"
          value={search}
          onValueChange={setSearch}
          placeholder="Subject or recipient"
        />
        <Button variant="flat" onPress={() => refetch()}>
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : (
        <Table aria-label="Email logs" className="w-full">
          <TableHeader>
            <TableColumn>Sent</TableColumn>
            <TableColumn>From</TableColumn>
            <TableColumn>To</TableColumn>
            <TableColumn>Subject</TableColumn>
            <TableColumn>Status</TableColumn>
            <TableColumn>Opened</TableColumn>
            <TableColumn>Source</TableColumn>
            <TableColumn>Actions</TableColumn>
          </TableHeader>
          <TableBody emptyContent="No emails found.">
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell>{log.sent_at ? new Date(log.sent_at).toLocaleString() : '—'}</TableCell>
                <TableCell className="max-w-[140px] truncate">{log.from_email}</TableCell>
                <TableCell className="max-w-[160px] truncate">
                  {(log.to_emails || []).join(', ')}
                </TableCell>
                <TableCell className="max-w-[200px] truncate">{log.subject}</TableCell>
                <TableCell>
                  <Chip size="sm" color={STATUS_COLOR[log.status] || 'default'} variant="flat">
                    {log.status}
                  </Chip>
                </TableCell>
                <TableCell>
                  {log.opened_at ? new Date(log.opened_at).toLocaleString() : '—'}
                </TableCell>
                <TableCell>{log.source}</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="light"
                      isLoading={resend.isPending}
                      onPress={() => resend.mutate(log.id)}
                    >
                      Resend
                    </Button>
                    <Button
                      size="sm"
                      variant="light"
                      onPress={() => renotify.mutate(log.id)}
                    >
                      Re-notify
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
