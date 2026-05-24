'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { submitApplication } from '@/lib/jobBoardApi';

type Props = {
  tenantSlug: string;
  jobSlug: string;
  jobTitle: string;
  brandColor: string;
};

export function ApplyForm({ tenantSlug, jobSlug, jobTitle, brandColor }: Props) {
  const router = useRouter();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const form = e.currentTarget;
    const fd = new FormData(form);
    try {
      const result = await submitApplication(tenantSlug, jobSlug, fd);
      if (result.redirect_url) {
        window.location.href = result.redirect_url;
        return;
      }
      setDone(true);
      setTimeout(() => router.push(`/${tenantSlug}/jobs/${jobSlug}`), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <p className="font-medium text-green-800">Application submitted</p>
        <p className="text-sm text-green-700 mt-1">Thank you for applying to {jobTitle}.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input type="text" name="website" className="hidden" tabIndex={-1} autoComplete="off" />
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">First name *</label>
          <input name="first_name" required className="w-full border rounded-md px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Last name</label>
          <input name="last_name" className="w-full border rounded-md px-3 py-2 text-sm" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Email *</label>
        <input name="email" type="email" required className="w-full border rounded-md px-3 py-2 text-sm" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Phone</label>
        <input name="phone" type="tel" className="w-full border rounded-md px-3 py-2 text-sm" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Resume (PDF or DOCX) *</label>
        <input
          name="resume_file"
          type="file"
          required
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="w-full text-sm"
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="w-full sm:w-auto px-6 py-3 rounded-md text-white font-medium text-sm disabled:opacity-60"
        style={{ backgroundColor: brandColor }}
      >
        {loading ? 'Submitting…' : 'Submit application'}
      </button>
      <p className="text-xs text-gray-500">
        <Link href={`/${tenantSlug}/jobs/${jobSlug}`} className="underline">
          Back to job description
        </Link>
      </p>
    </form>
  );
}
