/** Module-level frontend debug logging state (used by axios interceptors). */

let frontendDebugEnabled = false;
let userEmail = '';
let userRoles: string[] = [];

export function setFrontendDebugEnabled(enabled: boolean): void {
  frontendDebugEnabled = enabled;
}

export function isFrontendDebugEnabled(): boolean {
  return frontendDebugEnabled;
}

export function setDebugUserContext(ctx: { email: string; roles: string[] }): void {
  userEmail = ctx.email;
  userRoles = ctx.roles;
}

export function getDebugUserContext(): { email: string; roles: string[] } {
  return { email: userEmail, roles: userRoles };
}

const MAX_BODY_CHARS = 32 * 1024;

export function truncateForDebug(value: unknown): unknown {
  if (value == null) return value;
  try {
    const str = typeof value === 'string' ? value : JSON.stringify(value);
    if (str.length <= MAX_BODY_CHARS) {
      return typeof value === 'string' ? value : JSON.parse(str);
    }
    return `${str.slice(0, MAX_BODY_CHARS)}… [truncated ${str.length - MAX_BODY_CHARS} chars]`;
  } catch {
    return String(value).slice(0, MAX_BODY_CHARS);
  }
}

export function headersToRecord(
  headers: Record<string, unknown> | undefined
): Record<string, string> {
  if (!headers) return {};
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(headers)) {
    if (value == null) continue;
    out[key] = Array.isArray(value) ? value.join(', ') : String(value);
  }
  return out;
}
