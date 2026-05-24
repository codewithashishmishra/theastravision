'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody } from '@nextui-org/react';
import TrackerStatusBadge from '@/components/wfh/TrackerStatusBadge';
import { wfhApi } from '@/lib/wfhApi';

export default function TeamWFHSessionsPage() {
  const [team, setTeam] = useState<{ employee_id: string; name: string; online: boolean; session_status: string | null }[]>([]);

  useEffect(() => {
    wfhApi.teamSummary().then((r) => setTeam(r.data));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Team WFH Sessions</h1>
      <Card>
        <CardBody className="gap-4">
          {team.map((m) => (
            <div key={m.employee_id} className="flex justify-between border-b border-divider pb-3">
              <div>
                <p className="font-semibold">{m.name}</p>
                <p className="text-xs text-default-500">Session: {m.session_status || 'none'}</p>
              </div>
              <TrackerStatusBadge online={m.online} status={m.session_status} />
            </div>
          ))}
          {team.length === 0 && <p className="text-default-500">No reportees or no active data.</p>}
        </CardBody>
      </Card>
    </div>
  );
}
