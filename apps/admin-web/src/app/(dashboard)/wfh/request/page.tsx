'use client';

import { Card, CardBody, CardHeader } from '@nextui-org/react';
import WFHRequestForm from '@/components/wfh/WFHRequestForm';

export default function WFHRequestPage() {
  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">Request Work From Home</h1>
      <Card>
        <CardHeader>
          <p className="text-default-500 text-sm">
            Submit a WFH request for manager and HR approval. Tracking is only available after approval.
          </p>
        </CardHeader>
        <CardBody>
          <WFHRequestForm />
        </CardBody>
      </Card>
    </div>
  );
}
