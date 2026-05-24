'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Chip, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow } from '@nextui-org/react';
import { wfhApi } from '@/lib/wfhApi';
import { formatRegionalDateTime } from '@/lib/formatDateTime';

export default function TrackerDevicesPage() {
  const [devices, setDevices] = useState<Record<string, string>[]>([]);

  useEffect(() => {
    wfhApi.trackerDevices().then((r) => setDevices(r.data));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Tracker Devices</h1>
      <Card>
        <CardBody>
          <Table>
            <TableHeader>
              <TableColumn>Device</TableColumn>
              <TableColumn>OS</TableColumn>
              <TableColumn>App version</TableColumn>
              <TableColumn>Last seen</TableColumn>
              <TableColumn>Trusted</TableColumn>
            </TableHeader>
            <TableBody>
              {devices.map((d) => (
                <TableRow key={d.id}>
                  <TableCell>{d.device_name || d.device_uuid}</TableCell>
                  <TableCell>
                    {d.os_name} {d.os_version}
                  </TableCell>
                  <TableCell>{d.app_version}</TableCell>
                  <TableCell>{d.last_seen_at ? formatRegionalDateTime(d.last_seen_at) : '—'}</TableCell>
                  <TableCell>
                    <Chip size="sm" color={d.is_trusted ? 'success' : 'warning'}>
                      {d.is_trusted ? 'Trusted' : 'Untrusted'}
                    </Chip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
