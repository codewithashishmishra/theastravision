'use client';

import { Button, Chip, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from '@nextui-org/react';

export type WFHRequestRow = {
  id: string;
  employee_name?: string;
  start_date: string;
  end_date: string;
  reason: string;
  status: string;
  is_wfh_approved?: boolean;
};

type Props = {
  rows: WFHRequestRow[];
  showActions?: 'manager' | 'hr' | 'employee';
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onCancel?: (id: string) => void;
};

const statusColor = (s: string) => {
  if (s === 'hr_approved' || s === 'manager_approved') return 'success';
  if (s === 'rejected') return 'danger';
  if (s === 'pending') return 'warning';
  return 'default';
};

export default function WFHRequestTable({ rows, showActions, onApprove, onReject, onCancel }: Props) {
  return (
    <Table aria-label="WFH requests">
      <TableHeader>
        <TableColumn>Employee</TableColumn>
        <TableColumn>Dates</TableColumn>
        <TableColumn>Reason</TableColumn>
        <TableColumn>Status</TableColumn>
        <TableColumn>Actions</TableColumn>
      </TableHeader>
      <TableBody emptyContent="No requests">
        {rows.map((r) => (
          <TableRow key={r.id}>
            <TableCell>{r.employee_name || '—'}</TableCell>
            <TableCell>
              {r.start_date} → {r.end_date}
            </TableCell>
            <TableCell className="max-w-xs truncate">{r.reason}</TableCell>
            <TableCell>
              <Chip size="sm" color={statusColor(r.status)} variant="flat">
                {r.status.replace('_', ' ')}
              </Chip>
            </TableCell>
            <TableCell>
              <div className="flex gap-2">
                {showActions === 'employee' && r.status === 'pending' && (
                  <Button size="sm" variant="flat" color="danger" onPress={() => onCancel?.(r.id)}>
                    Cancel
                  </Button>
                )}
                {(showActions === 'manager' || showActions === 'hr') && ['pending', 'manager_approved'].includes(r.status) && (
                  <>
                    <Button size="sm" color="primary" onPress={() => onApprove?.(r.id)}>
                      Approve
                    </Button>
                    <Button size="sm" variant="flat" color="danger" onPress={() => onReject?.(r.id)}>
                      Reject
                    </Button>
                  </>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
