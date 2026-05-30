import api from '@/lib/axios';
import type { Role } from '@/config/menuConfig';
import { getPrimaryRole, resolvePostLoginRoute } from '@/lib/roleRouting';
import { setViewingTimezone, clearViewingTimezone } from '@/lib/formatDateTime';
import { clearAccessToken, setAccessToken } from '@/lib/tokenStore';
import { resetE2EESession } from '@/lib/e2ee/handshake';

export type AuthTenant = {
  id: string;
  name: string;
  email_domain: string;
  enabled_jurisdictions: string[];
  default_currency: string;
  subscription_plan?: 'starter' | 'professional' | 'enterprise';
};

export type AuthMeResponse = {
  email: string;
  display_name: string;
  roles: string[];
  tenant: AuthTenant | null;
  viewing_timezone?: string;
};

export async function fetchAuthMe(): Promise<AuthMeResponse> {
  const res = await api.get<AuthMeResponse>('/auth/me/');
  return res.data;
}

export function persistAuthSession(user: AuthMeResponse): Role {
  const primary = getPrimaryRole(user.roles);
  localStorage.setItem('user_role', primary);
  localStorage.setItem('user_roles', JSON.stringify(user.roles));
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('user_email', user.email);
    sessionStorage.setItem('user_name', user.display_name || user.email);
  }
  if (user.viewing_timezone) {
    setViewingTimezone(user.viewing_timezone);
  }
  if (user.tenant) {
    localStorage.setItem('tenant_id', user.tenant.id);
    localStorage.setItem('tenant_name', user.tenant.name);
    localStorage.setItem('tenant_email_domain', user.tenant.email_domain);
    localStorage.setItem('tenant_jurisdictions', JSON.stringify(user.tenant.enabled_jurisdictions ?? ['IN']));
    localStorage.setItem('tenant_currency', user.tenant.default_currency ?? 'INR');
    if (user.tenant.subscription_plan) {
      localStorage.setItem('tenant_plan', user.tenant.subscription_plan);
    } else {
      localStorage.setItem('tenant_plan', 'starter');
    }
  } else {
    localStorage.removeItem('tenant_id');
    localStorage.removeItem('tenant_name');
    localStorage.removeItem('tenant_email_domain');
    localStorage.removeItem('tenant_jurisdictions');
    localStorage.removeItem('tenant_currency');
  }
  return primary;
}

export function clearAuthSession(): void {
  clearAccessToken();
  resetE2EESession();
  localStorage.removeItem('user_role');
  localStorage.removeItem('user_roles');
  sessionStorage.removeItem('user_email');
  sessionStorage.removeItem('user_name');
  localStorage.removeItem('tenant_id');
  localStorage.removeItem('tenant_name');
  localStorage.removeItem('tenant_email_domain');
  localStorage.removeItem('tenant_jurisdictions');
  localStorage.removeItem('tenant_currency');
  localStorage.removeItem('tenant_plan');
  clearViewingTimezone();
}

export async function bootstrapAuthSession(): Promise<boolean> {
  const stored = typeof window !== 'undefined' ? sessionStorage.getItem('aastraa_access_token') : null;
  if (stored) {
    setAccessToken(stored);
    try {
      await loadAndPersistAuthSession();
      return true;
    } catch {
      /* fall through to refresh */
    }
  }
  try {
    const res = await api.post('/auth/token/refresh/', {});
    const access = res.data.access ?? res.data.access_token;
    if (!access) return false;
    setAccessToken(access);
    await loadAndPersistAuthSession();
    return true;
  } catch {
    return false;
  }
}
export async function loadAndPersistAuthSession(): Promise<{
  user: AuthMeResponse;
  homeRoute: string;
  primaryRole: Role;
}> {
  const user = await fetchAuthMe();
  const primaryRole = persistAuthSession(user);
  return {
    user,
    homeRoute: resolvePostLoginRoute(user),
    primaryRole,
  };
}
