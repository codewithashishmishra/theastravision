/** In-memory access token store; mirrored to sessionStorage for hard reload recovery. */

const SESSION_ACCESS_KEY = 'aastraa_access_token';

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  if (accessToken) return accessToken;
  if (typeof window !== 'undefined') {
    const stored = sessionStorage.getItem(SESSION_ACCESS_KEY);
    if (stored) {
      accessToken = stored;
      return stored;
    }
  }
  return null;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (typeof window !== 'undefined') {
    if (token) {
      sessionStorage.setItem(SESSION_ACCESS_KEY, token);
    } else {
      sessionStorage.removeItem(SESSION_ACCESS_KEY);
    }
  }
}

export function clearAccessToken(): void {
  accessToken = null;
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem(SESSION_ACCESS_KEY);
  }
}
