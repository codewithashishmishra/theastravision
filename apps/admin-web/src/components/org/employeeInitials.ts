/** Build display initials from employee name (e.g. Ashish Mishra → AM). */
export function getEmployeeInitials(firstName?: string, lastName?: string): string {
  const parts: string[] = [];
  if (firstName?.trim()) {
    parts.push(firstName.trim()[0]!.toUpperCase());
  }
  if (lastName?.trim()) {
    parts.push(lastName.trim()[0]!.toUpperCase());
  }
  return parts.join('') || '?';
}

export function getInitialsFromFullName(name: string): string {
  const tokens = name.trim().split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return '?';
  if (tokens.length === 1) return tokens[0]!.slice(0, 2).toUpperCase();
  return `${tokens[0]![0]}${tokens[tokens.length - 1]![0]}`.toUpperCase();
}
