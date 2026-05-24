'use client';

import { Card, CardBody, Chip, Spinner } from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { attendanceApi } from '@/lib/hrmsApi';

type LiveRow = {
  employee_id: string;
  employee_name: string;
  latitude: number;
  longitude: number;
  recorded_at: string;
  status: 'Active' | 'Stale';
  near_home: boolean;
};

export default function FieldTrackingPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['field-pings-live'],
    queryFn: async () => (await attendanceApi.fieldPings.live()).data as LiveRow[],
    refetchInterval: 60_000,
  });

  const rows = data ?? [];
  const first = rows[0];
  const mapUrl = first
    ? `https://www.openstreetmap.org/export/embed.html?marker=${first.latitude},${first.longitude}&zoom=13`
    : null;

  return (
    <div className="w-full flex flex-col gap-4">
      <h1 className="text-2xl font-bold">Field Tracking Map</h1>
      {isLoading ? <Spinner /> : null}
      {mapUrl && (
        <Card>
          <CardBody>
            <iframe title="field-tracking-map" src={mapUrl} className="w-full h-[360px] rounded-xl border-0" />
          </CardBody>
        </Card>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {rows.map((row) => (
          <Card key={row.employee_id}>
            <CardBody className="gap-2">
              <div className="font-semibold">{row.employee_name}</div>
              <div className="text-sm text-default-500">Last seen: {new Date(row.recorded_at).toLocaleString()}</div>
              <div className="flex gap-2">
                <Chip color={row.status === 'Active' ? 'success' : 'warning'}>{row.status}</Chip>
                {row.near_home && <Chip color="danger">Near home</Chip>}
              </div>
              <a
                className="text-primary text-sm underline"
                href={`https://www.openstreetmap.org/?mlat=${row.latitude}&mlon=${row.longitude}#map=14/${row.latitude}/${row.longitude}`}
                target="_blank"
                rel="noreferrer"
              >
                Open in map
              </a>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
}
