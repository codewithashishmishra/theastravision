'use client';

import React from 'react';

export default function DashboardLoading() {
  return (
    <div className="w-full h-[60vh] flex flex-col items-center justify-center gap-6 p-8">
      <div className="flex gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="w-14 h-14 rounded-2xl bg-content2 border border-divider animate-pulse"
          />
        ))}
      </div>
      <div className="flex flex-col items-center gap-2 w-full max-w-xs">
        <div className="h-7 w-48 rounded-lg bg-content2 animate-pulse" />
        <div className="h-4 w-36 rounded-md bg-content2/80 animate-pulse" />
      </div>
      <div className="w-64 h-1.5 bg-default-100 rounded-full overflow-hidden">
        <div className="h-full w-1/3 bg-primary/60 rounded-full animate-pulse" />
      </div>
    </div>
  );
}
