import { AxiosError } from 'axios';

export function parseApiError(err: unknown, fallback = 'Request failed'): string {
  if (err instanceof AxiosError) {
    const data = err.response?.data;
    if (typeof data === 'string' && data) return data;
    if (data && typeof data === 'object') {
      const d = data as Record<string, unknown>;
      if (typeof d.detail === 'string') return d.detail;
      if (Array.isArray(d.detail)) return d.detail.map(String).join(', ');
      if (typeof d.error === 'string') return d.error;
      if (typeof d.message === 'string') return d.message;
    }
    if (err.response?.status) return `${fallback} (HTTP ${err.response.status})`;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
