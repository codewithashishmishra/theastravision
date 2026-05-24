'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from '@nextui-org/react';
import { wfhApi } from '@/lib/wfhApi';

export default function TrackerSettingsPage() {
  const [settings, setSettings] = useState<{ policy?: Record<string, unknown>; app_versions?: { version: string; min_supported: string; is_mandatory: boolean }[] }>({});

  useEffect(() => {
    wfhApi.trackerSettings().then((r) => setSettings(r.data));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Tracker Settings</h1>
      <Card>
        <CardBody>
          <pre className="text-xs overflow-auto bg-default-100 p-4 rounded-lg">
            {JSON.stringify(settings.policy, null, 2)}
          </pre>
        </CardBody>
      </Card>
      <Card>
        <CardBody>
          <Table>
            <TableHeader>
              <TableColumn>Version</TableColumn>
              <TableColumn>Min supported</TableColumn>
              <TableColumn>Mandatory</TableColumn>
            </TableHeader>
            <TableBody>
              {(settings.app_versions || []).map((v) => (
                <TableRow key={v.version}>
                  <TableCell>{v.version}</TableCell>
                  <TableCell>{v.min_supported}</TableCell>
                  <TableCell>{v.is_mandatory ? 'Yes' : 'No'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
