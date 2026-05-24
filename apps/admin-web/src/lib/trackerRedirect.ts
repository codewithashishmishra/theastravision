/** Allowed redirect targets for desktop tracker OAuth-style callback (localhost only). */

export function isAllowedTrackerRedirect(url: string): boolean {
  try {
    const u = new URL(url);
    if (u.protocol !== 'http:') return false;
    const host = u.hostname.toLowerCase();
    if (host !== '127.0.0.1' && host !== 'localhost') return false;
    const port = Number(u.port || (u.protocol === 'http:' ? 80 : 443));
    if (port < 1 || port > 65535) return false;
    return u.pathname === '/callback' || u.pathname.endsWith('/callback');
  } catch {
    return false;
  }
}

export function buildTrackerCallbackUrl(
  trackerRedirect: string,
  params: {
    access_token: string;
    refresh_token?: string;
    state?: string;
    email?: string;
  }
): string {
  const url = new URL(trackerRedirect);
  url.searchParams.set('access_token', params.access_token);
  if (params.refresh_token) url.searchParams.set('refresh_token', params.refresh_token);
  if (params.state) url.searchParams.set('state', params.state);
  if (params.email) url.searchParams.set('email', params.email);
  return url.toString();
}
