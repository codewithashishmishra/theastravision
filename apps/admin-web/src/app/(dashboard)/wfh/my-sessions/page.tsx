'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Chip, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from '@nextui-org/react';
import { wfhApi } from '@/lib/wfhApi';
import { formatRegionalDateTime } from '@/lib/formatDateTime';

type Session = {
  id: string;
  start_time: string;
  end_time?: string;
  status: string;
  active_duration: number;
  idle_duration: number;
  screenshot_count: number;
};

export default function MySessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    wfhApi.sessionReport().then((r) => setSessions(r.data)).catch(() => setSessions([]));
  }, []);

  const fmt = (s: number) => `${Math.floor(s / 60)}m`;

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">My WFH Sessions</h1>
      <Card>
        <CardBody>
          <Table aria-label="Sessions">
            <TableHeader>
              <TableColumn>Start</TableColumn>
              <TableColumn>End</TableColumn>
              <TableColumn>Status</TableColumn>
              <TableColumn>Active</TableColumn>
              <TableColumn>Idle</TableColumn>
              <TableColumn>Screenshots</TableColumn>
            </TableHeader>
            <TableBody emptyContent="No sessions yet">
              {sessions.map((s) => (
                <TableRow key={s.id}>
                  <TableCell>{formatRegionalDateTime(s.start_time)}</TableCell>
                  <TableCell>{s.end_time ? formatRegionalDateTime(s.end_time) : '—'}</TableCell>
                  <TableCell>
                    <Chip size="sm" variant="flat">
                      {s.status}
                    </Chip>
                  </TableCell>
                  <TableCell>{fmt(s.active_duration)}</TableCell>
                  <TableCell>{fmt(s.idle_duration)}</TableCell>
                  <TableCell>{s.screenshot_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
