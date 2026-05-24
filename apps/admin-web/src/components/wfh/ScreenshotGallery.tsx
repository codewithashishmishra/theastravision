'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, CardHeader, Spinner } from '@nextui-org/react';
import ScreenshotThumb from '@/components/wfh/ScreenshotThumb';
import { parseApiError } from '@/lib/parseApiError';
import { wfhApi } from '@/lib/wfhApi';

type Shot = { id: string; captured_at: string; monitor_number: number };

export default function ScreenshotGallery({ sessionId }: { sessionId: string }) {
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    wfhApi
      .sessionScreenshots(sessionId)
      .then((r) => {
        setShots(r.data);
        setError(null);
      })
      .catch((e) => setError(parseApiError(e, 'Could not load screenshot list')))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <Spinner />;
  return (
    <Card>
      <CardHeader>Screenshot timeline</CardHeader>
      <CardBody className="flex flex-col gap-4">
        {error && (
          <p className="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">
            {error}
          </p>
        )}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {shots.map((s) => (
            <ScreenshotThumb
              key={s.id}
              screenshotId={s.id}
              monitor={s.monitor_number}
              capturedAt={s.captured_at}
            />
          ))}
        </div>
        {shots.length === 0 && !error && (
          <p className="text-default-500">No screenshots for this session.</p>
        )}
      </CardBody>
    </Card>
  );
}
