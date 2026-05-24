const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

import { createE2EEClient, e2eeJsonFetch, getBrowserE2EEClient } from './e2ee/fetchDecrypt';

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

/** Reuse one E2EE session for multiple server-side fetches on the same page. */
export async function createJobBoardE2EEClient() {
  return createE2EEClient();
}

export async function fetchPortalConfig(tenantSlug: string): Promise<PortalConfig> {
  return e2eeJsonFetch<PortalConfig>(`${hostedBase(tenantSlug)}/config/`);
}

export async function fetchJobs(
  tenantSlug: string,
  params?: Record<string, string>,
): Promise<JobListItem[]> {
  const qs = new URLSearchParams(params);
  const url = `${hostedBase(tenantSlug)}/jobs/${qs.toString() ? `?${qs}` : ''}`;
  const data = await e2eeJsonFetch<{ results?: JobListItem[] } | JobListItem[]>(url);
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function fetchJob(tenantSlug: string, jobSlug: string): Promise<JobDetail> {
  return e2eeJsonFetch<JobDetail>(`${hostedBase(tenantSlug)}/jobs/${jobSlug}/`);
}

export async function submitApplication(
  tenantSlug: string,
  jobSlug: string,
  formData: FormData,
): Promise<{ status: string; message?: string; redirect_url?: string }> {
  const client = getBrowserE2EEClient();
  const headers = await client.getRequestHeaders();
  const res = await fetch(`${hostedBase(tenantSlug)}/jobs/${jobSlug}/apply/`, {
    method: 'POST',
    body: formData,
    headers,
  });
  const data = await client.parseResponse<{ status: string; message?: string; redirect_url?: string; detail?: string }>(res);
  if (!res.ok) throw new Error(data.detail || 'Application failed');
  return data;
}
