'use client';

import { Card, CardBody, CardHeader } from '@nextui-org/react';

type Point = { time: string; label: string; type: 'heartbeat' | 'idle' | 'screenshot' };

export default function SessionTimeline({ points }: { points: Point[] }) {
  return (
    <Card>
      <CardHeader>Session timeline</CardHeader>
      <CardBody className="flex flex-col gap-2">
        {points.map((p, i) => (
          <div key={i} className="flex gap-3 text-sm">
            <span className="text-default-400 w-24">{p.time}</span>
            <span className={`font-medium ${p.type === 'idle' ? 'text-warning' : 'text-success'}`}>
              {p.label}
            </span>
          </div>
        ))}
        {points.length === 0 && <p className="text-default-500">No events</p>}
      </CardBody>
    </Card>
  );
}
