'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Input } from '@nextui-org/react';
import { wfhApi } from '@/lib/wfhApi';

export default function ScreenshotRetentionPage() {
  const [days, setDays] = useState('30');

  useEffect(() => {
    wfhApi.getPolicy().then((r) => setDays(String(r.data.screenshot_retention_days ?? 30)));
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Screenshot Retention</h1>
      <Card>
        <CardBody className="max-w-md gap-4">
          <p className="text-sm text-default-500">
            Screenshots are deleted automatically after the retention period (Celery job). Encrypted at rest.
          </p>
          <Input label="Retention days" value={days} isReadOnly description="Edit via HR WFH Policy" />
        </CardBody>
      </Card>
    </div>
  );
}
