'use client';

import React from 'react';
import { Button, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Chip, Spinner } from '@nextui-org/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceApi, unwrapList } from '@/lib/hrmsApi';

export default function ManagerAttendanceApprovalsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['attendance-regularizations-pending'],
    queryFn: async () => {
      const res = await attendanceApi.regularizations.list();
      return unwrapList<Record<string, unknown>>(res.data).filter((r) => r.status === 'Pending');
    },
  });

  const approve = useMutation({
    mutationFn: (id: string) => attendanceApi.regularizations.approve(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance-regularizations-pending'] }),
  });
  const reject = useMutation({
    mutationFn: (id: string) => attendanceApi.regularizations.reject(id, 'Rejected by manager'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance-regularizations-pending'] }),
  });

  return (
    <div className="w-full flex flex-col gap-6">
      <h1 className="text-2xl font-extrabold">Attendance Regularization Approvals</h1>
      <Table>
        <TableHeader>
          <TableColumn>EMPLOYEE</TableColumn>
          <TableColumn>DESCRIPTION</TableColumn>
          <TableColumn>STATUS</TableColumn>
          <TableColumn>ACTIONS</TableColumn>
        </TableHeader>
        <TableBody emptyContent={isLoading ? <Spinner /> : 'No pending requests'} items={data ?? []}>
          {(row) => (
            <TableRow key={String(row.id)}>
              <TableCell>{String(row.employee_name ?? row.employee)}</TableCell>
              <TableCell>{String(row.description || row.reason)}</TableCell>
              <TableCell><Chip size="sm">{String(row.status)}</Chip></TableCell>
              <TableCell>
                <Button size="sm" color="success" className="mr-2" onPress={() => approve.mutate(String(row.id))}>Approve</Button>
                <Button size="sm" color="danger" variant="flat" onPress={() => reject.mutate(String(row.id))}>Reject</Button>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
