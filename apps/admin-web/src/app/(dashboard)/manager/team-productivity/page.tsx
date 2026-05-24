'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from '@nextui-org/react';
import { wfhApi } from '@/lib/wfhApi';

export default function TeamProductivityPage() {
  const [rows, setRows] = useState<{ summary_date: string; total_active: number; total_idle: number; total_screenshots: number }[]>([]);

  useEffect(() => {
    wfhApi.productivityReport().then((r) => setRows(r.data));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Team Productivity</h1>
      <Card>
        <CardBody>
          <Table>
            <TableHeader>
              <TableColumn>Date</TableColumn>
              <TableColumn>Active (sec)</TableColumn>
              <TableColumn>Idle (sec)</TableColumn>
              <TableColumn>Screenshots</TableColumn>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.summary_date}>
                  <TableCell>{r.summary_date}</TableCell>
                  <TableCell>{r.total_active}</TableCell>
                  <TableCell>{r.total_idle}</TableCell>
                  <TableCell>{r.total_screenshots}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
