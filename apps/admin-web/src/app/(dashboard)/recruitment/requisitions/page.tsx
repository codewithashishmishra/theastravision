'use client';

import { JobsManager } from '@/components/recruitment/JobsManager';

export default function RequisitionsPage() {
  return (
    <JobsManager
      title="Job requisitions"
      description="Create and manage hiring requisitions. Set status to Open before publishing to the career board."
    />
  );
}
