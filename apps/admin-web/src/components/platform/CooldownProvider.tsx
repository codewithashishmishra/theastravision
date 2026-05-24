'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import api from '@/lib/axios';
import {
  fetchPlatformStatus,
  type PlatformStatus,
} from '@/lib/platformStatus';
import {
  flushOfflineQueue,
  getPendingCount,
  type QueuedMutation,
} from '@/lib/offlineMutationQueue';
import { useAuth } from '@/lib/AuthProvider';

type CooldownContextValue = {
  isCooldown: boolean;
  retryAfterSeconds: number;
  pendingCount: number;
  status: PlatformStatus | null;
  message: string;
  refreshStatus: () => Promise<void>;
};

const CooldownContext = createContext<CooldownContextValue | null>(null);

const COOLDOWN_MESSAGE =
  'System is temporarily unavailable for saves (cooling down). Your changes are stored locally and will sync automatically.';

export function CooldownProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAuthReady } = useAuth();
  const [status, setStatus] = useState<PlatformStatus | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const wasCooldown = useRef(false);

  const refreshPending = useCallback(async () => {
    setPendingCount(await getPendingCount());
  }, []);

  const refreshStatus = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const next = await fetchPlatformStatus();
      setStatus(next);

      if (wasCooldown.current && !next.cooldown_active) {
        await flushOfflineQueue(async (item: QueuedMutation) => {
          const base = api.defaults.baseURL ?? '';
          let path = item.url;
          if (base && path.startsWith(base)) {
            path = path.slice(base.length);
          }
          if (!path.startsWith('/')) path = `/${path}`;
          const headers = { ...item.headers };
          if (item.body) {
            headers['Content-Type'] = headers['Content-Type'] ?? 'application/json';
          }
          await api.request({
            method: item.method.toLowerCase() as 'post' | 'put' | 'patch' | 'delete',
            url: path,
            data: item.body ? JSON.parse(item.body) : undefined,
            headers,
          });
        });
      }
      wasCooldown.current = next.cooldown_active;
      await refreshPending();
    } catch {
      /* ignore polling errors */
    }
  }, [isAuthenticated, refreshPending]);

  useEffect(() => {
    if (!isAuthReady || !isAuthenticated) return;
    refreshStatus();
    const id = setInterval(refreshStatus, 12000);
    return () => clearInterval(id);
  }, [isAuthReady, isAuthenticated, refreshStatus]);

  useEffect(() => {
    const onQueued = () => refreshPending();
    window.addEventListener('aastraa-offline-queued', onQueued);
    return () => window.removeEventListener('aastraa-offline-queued', onQueued);
  }, [refreshPending]);

  const value = useMemo(
    () => ({
      isCooldown: status?.cooldown_active ?? false,
      retryAfterSeconds: status?.retry_after_seconds ?? 0,
      pendingCount,
      status,
      message: COOLDOWN_MESSAGE,
      refreshStatus,
    }),
    [status, pendingCount, refreshStatus]
  );

  return <CooldownContext.Provider value={value}>{children}</CooldownContext.Provider>;
}

export function useCooldown(): CooldownContextValue {
  const ctx = useContext(CooldownContext);
  if (!ctx) {
    return {
      isCooldown: false,
      retryAfterSeconds: 0,
      pendingCount: 0,
      status: null,
      message: '',
      refreshStatus: async () => {},
    };
  }
  return ctx;
}
