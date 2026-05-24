import axios, { type InternalAxiosRequestConfig } from 'axios';
import { enqueueMutation } from '@/lib/offlineMutationQueue';
import { clearAccessToken, getAccessToken, setAccessToken } from '@/lib/tokenStore';
import {
  getDebugUserContext,
  headersToRecord,
  isFrontendDebugEnabled,
  truncateForDebug,
} from '@/lib/debugLogStore';
import { decryptEnvelope, isE2EEEnvelope } from '@/lib/e2ee/crypto';
import { ensureE2EESession, rehandshake } from '@/lib/e2ee/handshake';
import { getAesKey, getSessionId, nextSeq } from '@/lib/e2ee/sessionStore';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1',
  withCredentials: true,
});

type AuthAxiosConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
  _skipAuthRefresh?: boolean;
  _skipCooldownQueue?: boolean;
  _skipDebugLog?: boolean;
  _e2eeRetry?: boolean;
};

function isAuthRefreshRequest(config?: AuthAxiosConfig): boolean {
  const url = config?.url ?? '';
  return url.includes('/auth/token/refresh/') || url.includes('/auth/login/');
}

function isHandshakeRequest(config?: AuthAxiosConfig): boolean {
  const url = config?.url ?? '';
  return url.includes('/public/e2ee/handshake');
}

function shouldSkipDebugLog(config?: AuthAxiosConfig): boolean {
  if (!config || config._skipDebugLog) return true;
  const url = config.url ?? '';
  return (
    url.includes('/platform/frontend-debug-log/') ||
    url.includes('/platform/status/') ||
    url.includes('/auth/token/refresh/') ||
    url.includes('/notifications/')
  );
}

function buildRequestUrl(config: AuthAxiosConfig): string {
  const base = config.baseURL ?? api.defaults.baseURL ?? '';
  const path = config.url ?? '';
  if (path.startsWith('http')) return path;
  const normalizedBase = base.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

function postDebugLogEntry(payload: Record<string, unknown>): void {
  void api
    .post('/platform/frontend-debug-log/', payload, { _skipDebugLog: true } as AuthAxiosConfig)
    .catch(() => {});
}

function logHttpDebug(
  direction: 'request' | 'response',
  config: AuthAxiosConfig,
  extra: {
    status?: number;
    body?: unknown;
    headers?: Record<string, unknown>;
    error?: string;
  } = {}
): void {
  if (!isFrontendDebugEnabled() || shouldSkipDebugLog(config)) return;

  const { email, roles } = getDebugUserContext();
  const method = (config.method ?? 'get').toUpperCase();
  const url = buildRequestUrl(config);
  const headers = headersToRecord(
    (extra.headers ?? config.headers) as Record<string, unknown> | undefined
  );
  const body =
    direction === 'request'
      ? truncateForDebug(config.data)
      : truncateForDebug(extra.body);

  postDebugLogEntry({
    direction,
    timestamp: new Date().toISOString(),
    user_email: email,
    roles,
    method,
    url,
    status: extra.status,
    headers,
    body,
    error: extra.error,
  });
}

function clearTokensAndRedirectToLogin(): void {
  clearAccessToken();
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login';
  }
}

export class PlatformCooldownError extends Error {
  retryAfterSeconds: number;
  constructor(message: string, retryAfterSeconds: number) {
    super(message);
    this.name = 'PlatformCooldownError';
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

api.interceptors.request.use(
  async (config) => {
    if (!isHandshakeRequest(config)) {
      await ensureE2EESession();
      const sid = getSessionId();
      if (sid) {
        config.headers = config.headers ?? {};
        config.headers['X-E2EE-Session'] = sid;
        config.headers['X-E2EE-Seq'] = String(nextSeq());
      }
    }
    const token = typeof window !== 'undefined' ? getAccessToken() : null;
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    logHttpDebug('request', config as AuthAxiosConfig);
    return config;
  },
  (error) => Promise.reject(error)
);

async function decryptResponseData(data: unknown): Promise<unknown> {
  if (!isE2EEEnvelope(data)) return data;
  const key = getAesKey();
  if (!key) throw new Error('Missing E2EE session key');
  return decryptEnvelope(key, data);
}

api.interceptors.response.use(
  async (response) => {
    if (response.data && isE2EEEnvelope(response.data)) {
      response.data = await decryptResponseData(response.data);
    }
    logHttpDebug('response', response.config as AuthAxiosConfig, {
      status: response.status,
      body: response.data,
      headers: response.headers as Record<string, unknown>,
    });
    return response;
  },
  async (error) => {
    const originalRequest = error.config as AuthAxiosConfig | undefined;
    if (!originalRequest) {
      return Promise.reject(error);
    }

    if (
      (error.response?.status === 428 || error.response?.status === 401) &&
      error.response?.data?.code?.toString().includes('E2EE') &&
      !originalRequest._e2eeRetry &&
      !isHandshakeRequest(originalRequest)
    ) {
      originalRequest._e2eeRetry = true;
      try {
        await rehandshake();
        return api(originalRequest);
      } catch {
        return Promise.reject(error);
      }
    }

    if (
      error.response?.status === 503 &&
      error.response?.data?.code === 'PLATFORM_COOLDOWN' &&
      !originalRequest._skipCooldownQueue
    ) {
      await enqueueMutation(originalRequest);
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('aastraa-offline-queued'));
      }
      const retryAfter = error.response?.data?.retry_after_seconds ?? 300;
      return Promise.reject(
        new PlatformCooldownError(
          error.response?.data?.message ??
            'System is cooling down. Your changes were saved locally and will sync when the system is back.',
          retryAfter
        )
      );
    }

    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      originalRequest._skipAuthRefresh ||
      isAuthRefreshRequest(originalRequest)
    ) {
      if (error.response?.data && isE2EEEnvelope(error.response.data)) {
        try {
          error.response.data = await decryptResponseData(error.response.data);
        } catch {
          /* keep encrypted envelope */
        }
      }
      if (error.response) {
        logHttpDebug('response', originalRequest, {
          status: error.response.status,
          body: error.response.data,
          headers: error.response.headers as Record<string, unknown>,
          error: error.message,
        });
      }
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const res = await api.post(
        '/auth/token/refresh/',
        {},
        { _skipAuthRefresh: true } as AuthAxiosConfig
      );
      const access = res.data.access ?? res.data.access_token;
      if (!access) {
        clearTokensAndRedirectToLogin();
        return Promise.reject(error);
      }
      setAccessToken(access);
      api.defaults.headers.common.Authorization = `Bearer ${access}`;
      originalRequest.headers.Authorization = `Bearer ${access}`;
      return api(originalRequest);
    } catch {
      clearTokensAndRedirectToLogin();
      return Promise.reject(error);
    }
  }
);

export default api;
