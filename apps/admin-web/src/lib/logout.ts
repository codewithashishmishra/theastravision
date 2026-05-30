import type { QueryClient } from '@tanstack/react-query';
import { clearAuthSession } from '@/lib/authSession';
import { getSessionId } from '@/lib/e2ee/sessionStore';
import { setDebugUserContext } from '@/lib/debugLogStore';

export type LogoutOptions = {
  queryClient?: QueryClient;
  /** When false, only clears client state (no navigation). Default true. */
  redirect?: boolean;
};

let logoutInFlight: Promise<void> | null = null;

/**
 * Full logout: revoke server session, clear tokens/E2EE/storage, optional React Query cache.
 */
export async function logout(options: LogoutOptions = {}): Promise<void> {
  if (logoutInFlight) return logoutInFlight;

  logoutInFlight = (async () => {
    const { queryClient, redirect = true } = options;

    try {
      const { default: api } = await import('@/lib/axios');
      const sid = getSessionId();
      await api.post('/auth/logout/', {}, {
        headers: sid ? { 'X-E2EE-Session': sid } : {},
        _skipAuthRefresh: true,
      } as Record<string, unknown>);
      delete api.defaults.headers.common.Authorization;
    } catch {
      /* still clear client state if API unreachable */
      try {
        const { default: api } = await import('@/lib/axios');
        delete api.defaults.headers.common.Authorization;
      } catch {
        /* ignore */
      }
    }

    clearAuthSession();
    setDebugUserContext({ email: '', roles: [] });

    if (queryClient) {
      await queryClient.cancelQueries();
      queryClient.clear();
    }

    if (
      redirect &&
      typeof window !== 'undefined' &&
      !window.location.pathname.startsWith('/login')
    ) {
      window.location.href = '/login';
    }
  })().finally(() => {
    logoutInFlight = null;
  });

  return logoutInFlight;
}
