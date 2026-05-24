'use client';

import { useRouter, useSearchParams } from 'next/navigation';

export function JobFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const update = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.push(`?${params.toString()}`);
  };

  return (
    <div className="flex flex-col sm:flex-row gap-3 mb-6">
      <input
        type="search"
        placeholder="Location"
        defaultValue={searchParams.get('location') ?? ''}
        className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1"
        onChange={(e) => update('location', e.target.value)}
      />
      <input
        type="search"
        placeholder="Department"
        defaultValue={searchParams.get('department') ?? ''}
        className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1"
        onChange={(e) => update('department', e.target.value)}
      />
      <select
        className="border border-gray-300 rounded-md px-3 py-2 text-sm"
        defaultValue={searchParams.get('employment_type') ?? ''}
        onChange={(e) => update('employment_type', e.target.value)}
      >
        <option value="">All types</option>
        <option value="Full-time">Full-time</option>
        <option value="Part-time">Part-time</option>
        <option value="Contract">Contract</option>
        <option value="Intern">Intern</option>
      </select>
    </div>
  );
}
