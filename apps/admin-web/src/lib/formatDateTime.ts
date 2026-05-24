const VIEWING_TIMEZONE_KEY = 'viewing_timezone';
const DEFAULT_VIEWING_TIMEZONE = 'Asia/Kolkata';

export function getViewingTimezone(): string {
  if (typeof window === 'undefined') {
    return DEFAULT_VIEWING_TIMEZONE;
  }
  return localStorage.getItem(VIEWING_TIMEZONE_KEY) || DEFAULT_VIEWING_TIMEZONE;
}

export function setViewingTimezone(timezone: string): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.setItem(VIEWING_TIMEZONE_KEY, timezone);
}

export function clearViewingTimezone(): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.removeItem(VIEWING_TIMEZONE_KEY);
}

function parseIso(value: string | null | undefined): Date | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatRegionalDateTime(
  value: string | null | undefined,
  timeZone?: string,
): string {
  const date = parseIso(value);
  if (!date) {
    return '—';
  }
  return date.toLocaleString(undefined, {
    timeZone: timeZone ?? getViewingTimezone(),
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function formatRegionalDate(
  value: string | null | undefined,
  timeZone?: string,
): string {
  const date = parseIso(value);
  if (!date) {
    return '—';
  }
  return date.toLocaleDateString(undefined, {
    timeZone: timeZone ?? getViewingTimezone(),
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatUtcDateTime(value: string | null | undefined): string {
  const date = parseIso(value);
  if (!date) {
    return '—';
  }
  return date.toLocaleString(undefined, {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}
