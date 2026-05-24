'use client';

import { JobsManager } from '@/components/recruitment/JobsManager';

export default function ActivePostingsPage() {
  return (
    <JobsManager
      title="Active postings"
      description="Open requisitions currently live or ready for the career board."
      filter={{ status: 'Open' }}
      showPublishActions
    />
  );
}
