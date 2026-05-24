'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { Role } from '@/config/menuConfig';
import {
  AuthMeResponse,
  bootstrapAuthSession,
  clearAuthSession,
  loadAndPersistAuthSession,
} from '@/lib/authSession';
import { getAccessToken } from '@/lib/tokenStore';
import { parseUserRoles } from '@/lib/roleRouting';
import { setDebugUserContext } from '@/lib/debugLogStore';

type AuthContextValue = {
  isAuthReady: boolean;
  isAuthenticated: boolean;
  user: AuthMeResponse | null;
  primaryRole: Role;
  roles: Role[];
  refreshAuth: () => Promise<boolean>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthMeResponse | null>(null);
  const [primaryRole, setPrimaryRole] = useState<Role>('Employee');
  const [roles, setRoles] = useState<Role[]>(['Employee']);

  const refreshAuth = useCallback(async (): Promise<boolean> => {
    let token = getAccessToken();
    if (!token) {
      const bootstrapped = await bootstrapAuthSession();
      if (!bootstrapped) {
        clearAuthSession();
        setIsAuthenticated(false);
        setUser(null);
        setPrimaryRole('Employee');
        setRoles(['Employee']);
        setDebugUserContext({ email: '', roles: [] });
        setIsAuthReady(true);
        router.replace('/login');
        return false;
      }
      token = getAccessToken();
    }

    try {
      const session = await loadAndPersistAuthSession();
      const parsedRoles = parseUserRoles(session.user.roles);
      setUser(session.user);
      setPrimaryRole(session.primaryRole);
      setRoles(parsedRoles);
      setDebugUserContext({
        email: session.user.email ?? '',
        roles: parsedRoles,
      });
      setIsAuthenticated(true);
      setIsAuthReady(true);
      return true;
    } catch {
      clearAuthSession();
      setIsAuthenticated(false);
      setUser(null);
      setPrimaryRole('Employee');
      setRoles(['Employee']);
      setDebugUserContext({ email: '', roles: [] });
      setIsAuthReady(true);
      router.replace('/login');
      return false;
    }
  }, [router]);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  const value = useMemo(
    () => ({
      isAuthReady,
      isAuthenticated,
      user,
      primaryRole,
      roles,
      refreshAuth,
    }),
    [isAuthReady, isAuthenticated, user, primaryRole, roles, refreshAuth]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}

export function useAuthReady(): boolean {
  const { isAuthReady, isAuthenticated } = useAuth();
  return isAuthReady && isAuthenticated;
}
