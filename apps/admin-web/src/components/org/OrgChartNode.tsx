'use client';

import { Avatar, Chip } from '@nextui-org/react';
import { getInitialsFromFullName } from './employeeInitials';

export type OrgChartNodeData = {
  id: string;
  name: string;
  initials: string;
  role: string;
  designation: string;
  avatar_url: string | null;
  employee_code: string;
};

type Props = {
  node: OrgChartNodeData;
  highlighted?: boolean;
};

export function OrgChartNode({ node, highlighted }: Props) {
  const initials = node.initials || getInitialsFromFullName(node.name);

  return (
    <div
      className={`flex min-w-[200px] max-w-[220px] flex-col items-center gap-2 rounded-2xl border bg-content1 px-4 py-3 shadow-md transition-colors ${
        highlighted ? 'border-primary ring-2 ring-primary/30' : 'border-divider'
      }`}
    >
      <Avatar
        src={node.avatar_url || undefined}
        name={initials}
        showFallback
        className="h-14 w-14 text-base font-bold"
        classNames={{ fallback: 'bg-primary/15 text-primary' }}
      />
      <div className="text-center">
        <p className="text-sm font-bold leading-tight text-foreground">{node.name}</p>
        <p className="text-xs text-default-500">{node.employee_code}</p>
        {node.designation ? (
          <p className="mt-1 text-xs text-default-600">{node.designation}</p>
        ) : null}
      </div>
      {node.role ? (
        <Chip size="sm" variant="flat" color="primary" className="max-w-full">
          <span className="truncate">{node.role}</span>
        </Chip>
      ) : null}
    </div>
  );
}
