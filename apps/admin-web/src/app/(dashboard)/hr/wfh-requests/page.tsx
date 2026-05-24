'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardBody, Tab, Tabs } from '@nextui-org/react';
import WFHRequestTable, { WFHRequestRow } from '@/components/wfh/WFHRequestTable';
import { parseApiError } from '@/lib/parseApiError';
import { wfhApi } from '@/lib/wfhApi';

export default function HRWFHRequestsPage() {
  const [tab, setTab] = useState<string>('all');
  const [allRows, setAllRows] = useState<WFHRequestRow[]>([]);
  const [pendingRows, setPendingRows] = useState<WFHRequestRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    const res = await wfhApi.listAllRequests();
    setAllRows(res.data);
  }, []);

  const loadPending = useCallback(async () => {
    const res = await wfhApi.pendingApprovals();
    setPendingRows(res.data);
  }, []);

  const load = useCallback(async () => {
    setError(null);
    try {
      await Promise.all([loadAll(), loadPending()]);
    } catch (e) {
      setError(parseApiError(e, 'Could not load WFH requests'));
    }
  }, [loadAll, loadPending]);

  useEffect(() => {
    load();
  }, [load]);

  const approve = async (id: string) => {
    setActionError(null);
    try {
      await wfhApi.hrApprove(id);
      await load();
    } catch (e) {
      setActionError(parseApiError(e, 'Approve failed'));
    }
  };

  const reject = async (id: string) => {
    setActionError(null);
    try {
      await wfhApi.reject(id);
      await load();
    } catch (e) {
      setActionError(parseApiError(e, 'Reject failed'));
    }
  };

  const rows = tab === 'pending' ? pendingRows : allRows;

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">HR — WFH Requests</h1>
      {error && (
        <p className="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</p>
      )}
      {actionError && (
        <p className="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{actionError}</p>
      )}
      <Tabs selectedKey={tab} onSelectionChange={(k) => setTab(String(k))}>
        <Tab key="all" title="All requests" />
        <Tab key="pending" title="Pending approval" />
      </Tabs>
      <Card>
        <CardBody>
          <WFHRequestTable
            rows={rows}
            showActions={tab === 'pending' ? 'hr' : undefined}
            onApprove={tab === 'pending' ? approve : undefined}
            onReject={tab === 'pending' ? reject : undefined}
          />
        </CardBody>
      </Card>
    </div>
  );
}
