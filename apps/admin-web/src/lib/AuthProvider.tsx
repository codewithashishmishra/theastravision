'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { Role } from '@/config/menuConfig';
import {
  AuthMeResponse,
  clearAuthSession,
  loadAndPersistAuthSession,
} from '@/lib/authSession';
import { parseUserRoles } from '@/lib/roleRouting';

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
    const token = localStorage.getItem('access_token');
    if (!token) {
      clearAuthSession();
      setIsAuthenticated(false);
      setUser(null);
      setPrimaryRole('Employee');
      setRoles(['Employee']);
      setIsAuthReady(true);
      router.replace('/login');
      return false;
    }

    try {
      const session = await loadAndPersistAuthSession();
      setUser(session.user);
      setPrimaryRole(session.primaryRole);
      setRoles(parseUserRoles(session.user.roles));
      setIsAuthenticated(true);
      setIsAuthReady(true);
      return true;
    } catch {
      clearAuthSession();
      setIsAuthenticated(false);
      setUser(null);
      setPrimaryRole('Employee');
      setRoles(['Employee']);
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
