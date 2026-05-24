'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardBody } from '@nextui-org/react';
import WFHRequestTable, { WFHRequestRow } from '@/components/wfh/WFHRequestTable';
import { wfhApi } from '@/lib/wfhApi';

export default function ManagerWFHApprovalsPage() {
  const [rows, setRows] = useState<WFHRequestRow[]>([]);

  const load = useCallback(async () => {
    const res = await wfhApi.pendingApprovals();
    setRows(res.data);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const approve = async (id: string) => {
    await wfhApi.managerApprove(id);
    load();
  };

  const reject = async (id: string) => {
    await wfhApi.reject(id);
    load();
  };

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">WFH Approvals</h1>
      <Card>
        <CardBody>
          <WFHRequestTable rows={rows} showActions="manager" onApprove={approve} onReject={reject} />
        </CardBody>
      </Card>
    </div>
  );
}
