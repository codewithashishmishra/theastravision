import api from './axios';

export type ColdCampaignListItem = {
  id: string;
  name: string;
  status: string;
  subject: string;
  from_name: string;
  from_email: string;
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  opened_count: number;
  is_paused: boolean;
  followup_count: number;
  created_at: string;
  updated_at: string;
};

export type ColdCampaignRecipient = {
  id: string;
  email: string;
  first_name: string;
  company: string;
  status: string;
  sent_at: string | null;
  opened_at: string | null;
  open_count: number;
  error_message: string;
  reply_status: string;
  last_reply_at: string | null;
  last_reply_snippet: string;
  followup_step_sent: number;
  next_followup_at: string | null;
};

export type ColdCampaignDetail = ColdCampaignListItem & {
  body_html: string;
  body_text: string;
  trial_url: string;
  generation_objective: string;
  followup_delay_days: number[];
  followup_subject_template: string;
  followup_body_html_template: string;
  recipients: ColdCampaignRecipient[];
};

export type ContentVariant = {
  id: string;
  variant_index: number;
  subject: string;
  body_html: string;
  body_text: string;
};

export type ContentBatch = {
  id: string;
  campaign: string | null;
  objective: string;
  model: string;
  created_at: string;
  variants: ContentVariant[];
};

export type LibraryVariant = ContentVariant & {
  batch_objective: string;
  batch_created_at: string;
  campaign_name: string | null;
};

export type ThreadMessage = {
  id: string;
  recipient_email: string;
  campaign_id: string;
  campaign_name: string;
  direction: string;
  subject: string;
  body_text: string;
  received_at: string;
  classification: string;
};

export type CampaignStats = {
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  opened_count: number;
  open_rate: number;
  recipients: ColdCampaignRecipient[];
};

const base = '/cold-campaigns';

export function apiErrorDetail(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const data = (err as { response?: { data?: { detail?: string } } }).response?.data;
    if (typeof data?.detail === 'string') return data.detail;
  }
  return 'Request failed.';
}

export const coldCampaignApi = {
  list: () => api.get<ColdCampaignListItem[]>(`${base}/`),
  get: (id: string) => api.get<ColdCampaignDetail>(`${base}/${id}/`),
  create: (data: {
    name: string;
    trial_url?: string;
    followup_count?: number;
    followup_delay_days?: number[];
  }) => api.post<ColdCampaignDetail>(`${base}/`, data),
  update: (id: string, data: Partial<ColdCampaignDetail>) =>
    api.patch<ColdCampaignDetail>(`${base}/${id}/`, data),
  loadDefaultTemplate: (id: string) =>
    api.post<ColdCampaignDetail>(`${base}/${id}/load-default-template/`),
  generateCopy: (id: string, tone = 'professional') =>
    api.post<ColdCampaignDetail>(`${base}/${id}/generate-copy/`, { tone }),
  generateVariations: (id: string, objective: 'sales' | 'quick_demo') =>
    api.post<ContentBatch>(`${base}/${id}/generate-variations/`, { objective }),
  contentLibrary: (objective?: string) =>
    api.get<LibraryVariant[]>(`${base}/content-library/`, {
      params: objective ? { objective } : undefined,
    }),
  applyVariant: (id: string, variantId: string) =>
    api.post<ColdCampaignDetail>(`${base}/${id}/apply-variant/`, { variant_id: variantId }),
  preview: (id: string, data?: { first_name?: string; company?: string }) =>
    api.post<{ subject: string; body_html: string; body_text: string }>(
      `${base}/${id}/preview/`,
      data || {},
    ),
  sendTest: (id: string) => api.post<{ detail: string }>(`${base}/${id}/send-test/`),
  send: (id: string) =>
    api.post<{ detail: string; status: string; pending: number }>(`${base}/${id}/send/`),
  pause: (id: string) => api.post<{ detail: string; is_paused: boolean }>(`${base}/${id}/pause/`),
  resume: (id: string) =>
    api.post<{ detail: string; is_paused: boolean }>(`${base}/${id}/resume/`),
  stats: (id: string) => api.get<CampaignStats>(`${base}/${id}/stats/`),
  listThreads: () => api.get<ThreadMessage[]>(`${base}/threads/`),
  campaignThreads: (id: string) => api.get<ThreadMessage[]>(`${base}/${id}/threads/`),
  importRecipients: (id: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post<{
      imported: number;
      skipped_duplicates: number;
      warnings: string[];
      total_recipients: number;
    }>(`${base}/${id}/import-recipients/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
