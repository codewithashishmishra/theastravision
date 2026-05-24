'use client';

import { Chip } from '@nextui-org/react';
import { formatUtcDateTime } from '@/lib/formatDateTime';

type Service = {
  service: string;
  state: string;
  uptime?: string | null;
  backend: string;
};

const stateColor = (state: string): 'success' | 'danger' | 'warning' | 'default' => {
  if (state === 'running' || state === 'active') return 'success';
  if (state === 'exited' || state === 'inactive' || state === 'failed') return 'danger';
  if (state === 'unknown' || state === 'unavailable') return 'warning';
  return 'default';
};

export function ServiceStatusGrid({ services }: { services: Service[] }) {
  if (!services.length) {
    return <p className="text-default-500 text-sm">No service status available.</p>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {services.map((svc) => (
        <div key={svc.service} className="border border-divider rounded-lg p-3 flex flex-col gap-2">
          <span className="font-semibold text-sm">{svc.service}</span>
          <Chip size="sm" color={stateColor(svc.state)} variant="flat">{svc.state}</Chip>
          {svc.uptime && <span className="text-xs text-default-400 truncate" title={svc.uptime}>Since {formatUtcDateTime(svc.uptime)}</span>}
          <span className="text-xs text-default-400">{svc.backend}</span>
        </div>
      ))}
    </div>
  );
}
