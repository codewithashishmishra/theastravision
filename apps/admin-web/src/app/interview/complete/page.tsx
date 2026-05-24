'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, CardBody } from '@nextui-org/react';

function CompleteContent() {
  const params = useSearchParams();
  const passed = params.get('passed') !== 'false';

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-white">
      <Card className="max-w-md bg-slate-800">
        <CardBody className="gap-4 p-8 text-center">
          <h1 className="text-2xl font-bold">{passed ? 'Thank you!' : 'Interview ended'}</h1>
          <p className="text-default-400">
            {passed
              ? 'Your responses have been recorded. HR will review your AI interview report.'
              : 'Your voice interview score was below the pass threshold. HR may contact you with next steps.'}
          </p>
        </CardBody>
      </Card>
    </div>
  );
}

export default function InterviewCompletePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950" />}>
      <CompleteContent />
    </Suspense>
  );
}
