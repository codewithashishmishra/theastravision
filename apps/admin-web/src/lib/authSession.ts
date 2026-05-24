import api from '@/lib/axios';
import type { Role } from '@/config/menuConfig';
import { getPrimaryRole, resolvePostLoginRoute } from '@/lib/roleRouting';

export type AuthTenant = {
  id: string;
  name: string;
  email_domain: string;
};

export type AuthMeResponse = {
  email: string;
  display_name: string;
  roles: string[];
  tenant: AuthTenant | null;
};

export async function fetchAuthMe(): Promise<AuthMeResponse> {
  const res = await api.get<AuthMeResponse>('/auth/me/');
  return res.data;
}

export function persistAuthSession(user: AuthMeResponse): Role {
  const primary = getPrimaryRole(user.roles);
  localStorage.setItem('user_role', primary);
  localStorage.setItem('user_roles', JSON.stringify(user.roles));
  localStorage.setItem('user_email', user.email);
  localStorage.setItem('user_name', user.display_name || user.email);
  if (user.tenant) {
    localStorage.setItem('tenant_id', user.tenant.id);
    localStorage.setItem('tenant_name', user.tenant.name);
    localStorage.setItem('tenant_email_domain', user.tenant.email_domain);
  } else {
    localStorage.removeItem('tenant_id');
    localStorage.removeItem('tenant_name');
    localStorage.removeItem('tenant_email_domain');
  }
  return primary;
}

export function clearAuthSession(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_role');
  localStorage.removeItem('user_roles');
  localStorage.removeItem('user_email');
  localStorage.removeItem('user_name');
  localStorage.removeItem('tenant_id');
  localStorage.removeItem('tenant_name');
  localStorage.removeItem('tenant_email_domain');
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
