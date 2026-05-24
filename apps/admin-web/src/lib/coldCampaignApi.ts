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
};

export type ColdCampaignDetail = ColdCampaignListItem & {
  body_html: string;
  body_text: string;
  trial_url: string;
  recipients: ColdCampaignRecipient[];
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

export const coldCampaignApi = {
  list: () => api.get<ColdCampaignListItem[]>(`${base}/`),
  get: (id: string) => api.get<ColdCampaignDetail>(`${base}/${id}/`),
  create: (data: { name: string; trial_url?: string }) => api.post<ColdCampaignDetail>(`${base}/`, data),
  update: (id: string, data: Partial<ColdCampaignDetail>) =>
    api.patch<ColdCampaignDetail>(`${base}/${id}/`, data),
  loadDefaultTemplate: (id: string) =>
    api.post<ColdCampaignDetail>(`${base}/${id}/load-default-template/`),
  generateCopy: (id: string, tone = 'professional') =>
    api.post<ColdCampaignDetail>(`${base}/${id}/generate-copy/`, { tone }),
  preview: (id: string, data?: { first_name?: string; company?: string }) =>
    api.post<{ subject: string; body_html: string; body_text: string }>(
      `${base}/${id}/preview/`,
      data || {},
    ),
  sendTest: (id: string) => api.post<{ detail: string }>(`${base}/${id}/send-test/`),
  send: (id: string) => api.post<{ detail: string; status: string; pending: number }>(`${base}/${id}/send/`),
  stats: (id: string) => api.get<CampaignStats>(`${base}/${id}/stats/`),
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
