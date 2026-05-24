import { Suspense } from 'react';
import Link from 'next/link';
import { CareerHeader } from '@/components/CareerHeader';
import { JobFilters } from '@/components/JobFilters';
import { fetchJobs, fetchPortalConfig } from '@/lib/jobBoardApi';

type Props = {
  params: Promise<{ tenantSlug: string }>;
  searchParams: Promise<Record<string, string | undefined>>;
};

export default async function CareersListPage({ params, searchParams }: Props) {
  const { tenantSlug } = await params;
  const filters = await searchParams;
  const config = await fetchPortalConfig(tenantSlug);
  const jobs = await fetchJobs(tenantSlug, {
    location: filters.location ?? '',
    department: filters.department ?? '',
    employment_type: filters.employment_type ?? '',
  });
  const brand = config.primary_color || '#2563eb';

  return (
    <div className="min-h-screen bg-gray-50">
      <CareerHeader config={config} />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <h2 className="text-lg font-semibold mb-1">Open positions</h2>
        <p className="text-sm text-gray-500 mb-6">{jobs.length} role{jobs.length !== 1 ? 's' : ''}</p>
        <Suspense fallback={null}>
          <JobFilters />
        </Suspense>
        <ul className="space-y-3">
          {jobs.map((job) => (
            <li key={job.id}>
              <Link
                href={`/${tenantSlug}/jobs/${job.slug}`}
                className="block bg-white border border-gray-200 rounded-lg p-5 hover:border-gray-300 hover:shadow-sm transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-lg">{job.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {[job.location, job.department, job.employment_type, job.work_mode]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                  </div>
                  <span
                    className="text-sm font-medium shrink-0"
                    style={{ color: brand }}
                  >
                    View role →
                  </span>
                </div>
              </Link>
            </li>
          ))}
          {jobs.length === 0 && (
            <li className="text-center py-12 text-gray-500 bg-white rounded-lg border">
              No open positions match your filters.
            </li>
          )}
        </ul>
      </main>
    </div>
  );
}
