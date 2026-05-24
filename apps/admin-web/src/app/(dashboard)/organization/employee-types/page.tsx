'use client';

import { ResourcePage } from '@/components/crud/ResourcePage';

const config = {
  title: 'Employee Types',
  endpoint: '/employees/employee-types/',
  queryKey: 'employee-types',
  columns: [
    { key: 'name', label: 'NAME' },
    { key: 'code', label: 'CODE' },
    { key: 'enable_live_tracking', label: 'LIVE TRACKING' },
    { key: 'require_selfie_on_punch', label: 'SELFIE REQUIRED' },
  ],
  formFields: [
    { key: 'name', label: 'Name', type: 'text', required: true },
    { key: 'code', label: 'Code', type: 'text', required: true },
    { key: 'tracking_interval_minutes', label: 'Tracking Interval (minutes)', type: 'number', required: true },
    { key: 'home_exclusion_radius_meters', label: 'Home Exclusion Radius (m)', type: 'number', required: true },
  ],
} as const;

export default function EmployeeTypesPage() {
  return (
    <div className="w-full flex flex-col gap-4">
      <p className="text-sm text-default-500">
        Configure type-level flags from API defaults. For full boolean flag editing, use backend API directly in this phase.
      </p>
      <ResourcePage config={config} />
    </div>
  );
}
