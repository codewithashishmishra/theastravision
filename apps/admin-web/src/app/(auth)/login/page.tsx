import React, { Suspense } from 'react';
import MultiLogin from '@/components/auth/MultiLogin';

function LoginFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <p className="text-default-500">Loading…</p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <MultiLogin />
    </Suspense>
  );
}
