'use client';

import { Chip } from '@nextui-org/react';

export default function TrackerStatusBadge({ online, status }: { online?: boolean; status?: string | null }) {
  if (online) {
    return (
      <Chip color="success" variant="dot" size="sm">
        Tracking Active
      </Chip>
    );
  }
  if (status === 'paused') {
    return (
      <Chip color="warning" variant="flat" size="sm">
        Paused
      </Chip>
    );
  }
  return (
    <Chip color="default" variant="flat" size="sm">
      Offline
    </Chip>
  );
}
