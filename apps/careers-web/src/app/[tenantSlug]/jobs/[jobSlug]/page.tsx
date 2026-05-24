import Link from 'next/link';
import { notFound } from 'next/navigation';
import { CareerHeader } from '@/components/CareerHeader';
import { fetchJob, fetchPortalConfig } from '@/lib/jobBoardApi';

type Props = {
  params: Promise<{ tenantSlug: string; jobSlug: string }>;
};

export default async function JobDetailPage({ params }: Props) {
  const { tenantSlug, jobSlug } = await params;
  let config;
  let job;
  try {
    [config, job] = await Promise.all([
      fetchPortalConfig(tenantSlug),
      fetchJob(tenantSlug, jobSlug),
    ]);
  } catch {
    notFound();
  }

  const brand = config.primary_color || '#2563eb';
  const applyHref = job.use_external_apply && job.external_apply_url
    ? job.external_apply_url
    : `/${tenantSlug}/jobs/${jobSlug}/apply`;

  return (
    <div className="min-h-screen bg-gray-50">
      <CareerHeader config={config} />
      <main className="max-w-3xl mx-auto px-4 py-8">
        <Link href={`/${tenantSlug}`} className="text-sm text-gray-500 hover:text-gray-800">
          ← All jobs
        </Link>
        <article className="mt-4 bg-white border border-gray-200 rounded-lg p-6 sm:p-8">
          <h1 className="text-2xl font-bold">{job.title}</h1>
          <p className="text-sm text-gray-500 mt-2">
            {[job.location, job.department, job.employment_type, job.work_mode]
              .filter(Boolean)
              .join(' · ')}
          </p>
          <div
            className="job-description mt-8 prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: job.description_html }}
          />
          <div className="mt-10 pt-6 border-t sticky bottom-0 bg-white">
            <a
              href={applyHref}
              className="inline-block px-6 py-3 rounded-md text-white font-medium text-sm"
              style={{ backgroundColor: brand }}
              {...(job.use_external_apply ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
            >
              Apply for this job
            </a>
          </div>
        </article>
      </main>
    </div>
  );
}
