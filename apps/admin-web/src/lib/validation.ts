/** Shared client-side form validation helpers. */

export type FieldError = string | undefined;

export function validateRequired(value: string, label = 'This field'): FieldError {
  if (!value.trim()) return `${label} is required.`;
  return undefined;
}

export function validateEmail(value: string): FieldError {
  if (!value.trim()) return 'Email is required.';
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(value.trim())) return 'Enter a valid email address.';
  return undefined;
}

/** Indian mobile: exactly 10 digits. */
export function validatePhoneIN(value: string, required = false): FieldError {
  const digits = value.replace(/\D/g, '');
  if (!digits) return required ? 'Phone number is required.' : undefined;
  if (!/^\d{10}$/.test(digits)) return 'Phone must be exactly 10 digits.';
  return undefined;
}

export function validateNumber(
  value: string,
  opts: { min?: number; max?: number; label?: string; required?: boolean } = {},
): FieldError {
  const label = opts.label ?? 'Value';
  if (!value.trim()) return opts.required !== false ? `${label} is required.` : undefined;
  const n = Number(value);
  if (Number.isNaN(n)) return `${label} must be a number.`;
  if (opts.min !== undefined && n < opts.min) return `${label} must be at least ${opts.min}.`;
  if (opts.max !== undefined && n > opts.max) return `${label} must be at most ${opts.max}.`;
  return undefined;
}

export function validateDateNotFuture(value: string, label = 'Date'): FieldError {
  if (!value) return undefined;
  const today = new Date().toISOString().slice(0, 10);
  if (value > today) return `${label} cannot be in the future.`;
  return undefined;
}

export function validateDateRange(start: string, end: string): FieldError {
  if (start && end && end < start) return 'End date must be on or after start date.';
  return undefined;
}

export function validateEmployeeCode(value: string): FieldError {
  const err = validateRequired(value, 'Employee code');
  if (err) return err;
  if (value.trim().length > 32) return 'Employee code must be at most 32 characters.';
  return undefined;
}
