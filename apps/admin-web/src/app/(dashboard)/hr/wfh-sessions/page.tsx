'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from '@nextui-org/react';
import ScreenshotGallery from '@/components/wfh/ScreenshotGallery';
import { parseApiError } from '@/lib/parseApiError';
import { wfhApi } from '@/lib/wfhApi';
import { formatRegionalDateTime } from '@/lib/formatDateTime';

type Session = {
  id: string;
  start_time: string;
  status: string;
  employee: string;
  employee_name?: string;
  screenshot_count: number;
  task_title?: string;
  task_description?: string;
};

export default function HRWFHSessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    wfhApi
      .sessionReport()
      .then((r) => {
        setSessions(r.data);
        setError(null);
      })
      .catch((e) => setError(parseApiError(e, 'Could not load WFH sessions')));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">WFH Sessions</h1>
      {error && (
        <p className="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</p>
      )}
      <Card>
        <CardBody>
          <Table
            selectionMode="single"
            onSelectionChange={(k) => setSelectedSession(Array.from(k)[0] as string)}
            aria-label="WFH sessions"
          >
            <TableHeader>
              <TableColumn>Start</TableColumn>
              <TableColumn>Employee</TableColumn>
              <TableColumn>Task</TableColumn>
              <TableColumn>Status</TableColumn>
              <TableColumn>Screenshots</TableColumn>
            </TableHeader>
            <TableBody emptyContent="No work sessions yet. Start tracking from the desktop app.">
              {sessions.map((s) => (
                <TableRow key={s.id}>
                  <TableCell>{formatRegionalDateTime(s.start_time)}</TableCell>
                  <TableCell>{s.employee_name || '—'}</TableCell>
                  <TableCell className="max-w-xs truncate">{s.task_title || '—'}</TableCell>
                  <TableCell>{s.status}</TableCell>
                  <TableCell>{s.screenshot_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
      {selectedSession && <ScreenshotGallery sessionId={selectedSession} />}
    </div>
  );
}
