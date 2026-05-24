import api from '@/lib/axios';

export type PlatformStatus = {
  cooldown_active: boolean;
  cooldown_until: string | null;
  retry_after_seconds: number;
  cpu_percent: number;
  ram_percent: number;
  cpu_threshold: number;
  ram_threshold: number;
  near_threshold: boolean;
  frontend_debug_enabled?: boolean;
};

export async function fetchPlatformStatus(): Promise<PlatformStatus> {
  const res = await api.get<PlatformStatus>('/platform/status/');
  return res.data;
}

export function isPlatformCooldownError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const err = error as { response?: { status?: number; data?: { code?: string } } };
  return (
    err.response?.status === 503 &&
    err.response?.data?.code === 'PLATFORM_COOLDOWN'
  );
}
