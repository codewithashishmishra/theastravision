const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export type PortalConfig = {
  tenant_name: string;
  slug: string;
  logo_url: string;
  primary_color: string;
  company_blurb: string;
};

export type JobListItem = {
  id: string;
  slug: string;
  title: string;
  location: string;
  department: string | null;
  employment_type: string;
  work_mode: string;
  published_at: string | null;
  apply_deadline: string | null;
  external_apply_url: string | null;
};

export type JobDetail = JobListItem & {
  description_html: string;
  description_text: string;
  headcount: number;
  use_external_apply: boolean;
};

function hostedBase(tenantSlug: string) {
  return `${API_BASE}/public/job-board/hosted/${tenantSlug}`;
}

export async function fetchPortalConfig(tenantSlug: string): Promise<PortalConfig> {
  const res = await fetch(`${hostedBase(tenantSlug)}/config/`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Career portal not found');
  return res.json();
}

export async function fetchJobs(
  tenantSlug: string,
  params?: Record<string, string>,
): Promise<JobListItem[]> {
  const qs = new URLSearchParams(params);
  const url = `${hostedBase(tenantSlug)}/jobs/${qs.toString() ? `?${qs}` : ''}`;
  const res = await fetch(url, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error('Failed to load jobs');
  const data = await res.json();
  return data.results ?? [];
}

export async function fetchJob(tenantSlug: string, jobSlug: string): Promise<JobDetail> {
  const res = await fetch(`${hostedBase(tenantSlug)}/jobs/${jobSlug}/`, {
    next: { revalidate: 30 },
  });
  if (!res.ok) throw new Error('Job not found');
  return res.json();
}

export async function submitApplication(
  tenantSlug: string,
  jobSlug: string,
  formData: FormData,
): Promise<{ status: string; message?: string; redirect_url?: string }> {
  const res = await fetch(`${hostedBase(tenantSlug)}/jobs/${jobSlug}/apply/`, {
    method: 'POST',
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Application failed');
  return data;
}
