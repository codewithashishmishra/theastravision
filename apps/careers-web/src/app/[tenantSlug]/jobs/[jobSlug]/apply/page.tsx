import Link from 'next/link';
import { notFound } from 'next/navigation';
import { CareerHeader } from '@/components/CareerHeader';
import { fetchJob, fetchPortalConfig } from '@/lib/jobBoardApi';
import { ApplyForm } from './ApplyForm';

type Props = {
  params: Promise<{ tenantSlug: string; jobSlug: string }>;
};

export default async function ApplyPage({ params }: Props) {
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

  if (job.use_external_apply && job.external_apply_url) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <a href={job.external_apply_url} className="text-blue-600 underline">
          Continue to external application
        </a>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <CareerHeader config={config} />
      <main className="max-w-lg mx-auto px-4 py-8">
        <Link href={`/${tenantSlug}/jobs/${jobSlug}`} className="text-sm text-gray-500">
          ← {job.title}
        </Link>
        <h1 className="text-xl font-bold mt-4">Apply for {job.title}</h1>
        <div className="mt-6 bg-white border rounded-lg p-6">
          <ApplyForm
            tenantSlug={tenantSlug}
            jobSlug={jobSlug}
            jobTitle={job.title}
            brandColor={config.primary_color || '#2563eb'}
          />
        </div>
      </main>
    </div>
  );
}
