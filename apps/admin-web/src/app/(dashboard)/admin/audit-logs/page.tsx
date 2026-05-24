'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from '@nextui-org/react';
import { wfhApi } from '@/lib/wfhApi';

export default function TrackerAuditLogsPage() {
  const [logs, setLogs] = useState<{ action: string; entity_type: string; created_at: string; ip_address: string }[]>([]);

  useEffect(() => {
    wfhApi.auditLogs().then((r) => setLogs(r.data));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Tracker Audit Logs</h1>
      <Card>
        <CardBody>
          <Table>
            <TableHeader>
              <TableColumn>Time</TableColumn>
              <TableColumn>Action</TableColumn>
              <TableColumn>Entity</TableColumn>
              <TableColumn>IP</TableColumn>
            </TableHeader>
            <TableBody>
              {logs.map((l) => (
                <TableRow key={`${l.created_at}-${l.action}`}>
                  <TableCell>{new Date(l.created_at).toLocaleString()}</TableCell>
                  <TableCell>{l.action}</TableCell>
                  <TableCell>{l.entity_type}</TableCell>
                  <TableCell>{l.ip_address}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
