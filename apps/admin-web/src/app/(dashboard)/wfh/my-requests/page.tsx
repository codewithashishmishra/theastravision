'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardBody } from '@nextui-org/react';
import WFHRequestTable, { WFHRequestRow } from '@/components/wfh/WFHRequestTable';
import { wfhApi } from '@/lib/wfhApi';

export default function MyWFHRequestsPage() {
  const [rows, setRows] = useState<WFHRequestRow[]>([]);

  const load = useCallback(async () => {
    const res = await wfhApi.listMyRequests();
    setRows(res.data);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const cancel = async (id: string) => {
    await wfhApi.cancel(id);
    load();
  };

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">My WFH Requests</h1>
      <Card>
        <CardBody>
          <WFHRequestTable rows={rows} showActions="employee" onCancel={cancel} />
        </CardBody>
      </Card>
    </div>
  );
}
