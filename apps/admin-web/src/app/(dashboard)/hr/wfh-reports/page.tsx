'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody } from '@nextui-org/react';
import ExportButton from '@/components/wfh/ExportButton';
import { parseApiError } from '@/lib/parseApiError';
import { wfhApi } from '@/lib/wfhApi';

export default function HRWFHReportsPage() {
  const [dash, setDash] = useState<Record<string, number>>({});
  const [productivity, setProductivity] = useState<unknown[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([wfhApi.dashboard(), wfhApi.productivityReport()])
      .then(([d, p]) => {
        setDash(d.data);
        setProductivity(p.data);
        setError(null);
      })
      .catch((e) => setError(parseApiError(e, 'Could not load WFH reports')));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-extrabold">WFH Reports</h1>
        <ExportButton data={productivity} filename="wfh-productivity" />
      </div>
      {error && (
        <p className="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</p>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <p className="text-sm text-default-500">Approved WFH today</p>
            <p className="text-2xl font-bold">{dash.approved_wfh_today ?? 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-default-500">Active sessions</p>
            <p className="text-2xl font-bold">{dash.active_sessions ?? 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-default-500">Pending approvals</p>
            <p className="text-2xl font-bold">{dash.pending_approvals ?? 0}</p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
