'use client';

import { redirect } from 'next/navigation';

export default function LegacyAuditDashboardPage() {
  redirect('/dashboards/audit');
}
