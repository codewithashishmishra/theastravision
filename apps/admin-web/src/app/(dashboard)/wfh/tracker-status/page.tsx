'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, CardHeader, Link } from '@nextui-org/react';
import TrackerStatusBadge from '@/components/wfh/TrackerStatusBadge';
import { wfhApi } from '@/lib/wfhApi';

export default function TrackerStatusPage() {
  const [dash, setDash] = useState<{ approved_wfh_today?: number; active_sessions?: number }>({});
  const [team, setTeam] = useState<{ name: string; online: boolean; session_status: string | null }[]>([]);

  useEffect(() => {
    wfhApi.dashboard().then((r) => setDash(r.data)).catch(() => {});
    wfhApi.teamSummary().then((r) => setTeam(r.data)).catch(() => setTeam([]));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">WFH Tracker Status</h1>
      <Card>
        <CardHeader>
          <p className="font-semibold">Desktop tracker</p>
        </CardHeader>
        <CardBody className="gap-4">
          <p className="text-default-600 text-sm">
            Install the Aastraa WFH Tracker desktop app. You must manually start tracking when WFH begins.
            The app shows a visible &quot;Tracking Active&quot; status — never silent monitoring.
          </p>
          <Link href="#" className="text-primary text-sm">
            Download tracker (configure TrackerAppVersion in admin)
          </Link>
          <div className="flex gap-4 flex-wrap">
            <TrackerStatusBadge online={(dash.active_sessions || 0) > 0} />
            <span className="text-sm text-default-500">
              Approved WFH today: {dash.approved_wfh_today ?? 0}
            </span>
          </div>
        </CardBody>
      </Card>
      {team.length > 0 && (
        <Card>
          <CardHeader>Team online status</CardHeader>
          <CardBody className="gap-2">
            {team.map((m) => (
              <div key={m.name} className="flex justify-between items-center">
                <span>{m.name}</span>
                <TrackerStatusBadge online={m.online} status={m.session_status} />
              </div>
            ))}
          </CardBody>
        </Card>
      )}
    </div>
  );
}
