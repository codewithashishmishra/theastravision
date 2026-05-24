import axios, { type InternalAxiosRequestConfig } from 'axios';
import { enqueueMutation } from '@/lib/offlineMutationQueue';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1',
});

type AuthAxiosConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
  _skipAuthRefresh?: boolean;
  _skipCooldownQueue?: boolean;
};

function isAuthRefreshRequest(config?: AuthAxiosConfig): boolean {
  const url = config?.url ?? '';
  return url.includes('/auth/token/refresh/') || url.includes('/auth/login/');
}

function clearTokensAndRedirectToLogin(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
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
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as AuthAxiosConfig | undefined;
    if (!originalRequest) {
      return Promise.reject(error);
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
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      clearTokensAndRedirectToLogin();
      return Promise.reject(error);
    }

    try {
      const res = await api.post(
        '/auth/token/refresh/',
        { refresh: refreshToken },
        { _skipAuthRefresh: true } as AuthAxiosConfig
      );
      const access = res.data.access ?? res.data.access_token;
      if (!access) {
        clearTokensAndRedirectToLogin();
        return Promise.reject(error);
      }
      localStorage.setItem('access_token', access);
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
