export type Jurisdiction = 'IN' | 'US' | 'CA';

export const JURISDICTION_LABELS: Record<Jurisdiction, string> = {
  IN: 'India',
  US: 'United States',
  CA: 'Canada',
};

export function setStoredJurisdictions(jurisdictions: Jurisdiction[]): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('tenant_jurisdictions', JSON.stringify(jurisdictions));
}

export function getStoredJurisdictions(): Jurisdiction[] {
  if (typeof window === 'undefined') return ['IN'];
  try {
    const raw = localStorage.getItem('tenant_jurisdictions');
    if (!raw) return ['IN'];
    const parsed = JSON.parse(raw) as string[];
    return parsed.filter((j): j is Jurisdiction => j === 'IN' || j === 'US' || j === 'CA');
  } catch {
    return ['IN'];
  }
}

export function menuVisibleForJurisdictions(
  itemJurisdictions: Jurisdiction[] | undefined,
  tenantJurisdictions: Jurisdiction[],
): boolean {
  if (!itemJurisdictions || itemJurisdictions.length === 0) return true;
  return itemJurisdictions.some((j) => tenantJurisdictions.includes(j));
}
