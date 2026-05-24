import { menuConfig, profileNavItem, MenuItem, Role } from '@/config/menuConfig';

function collectMenuItems(): MenuItem[] {
  const items: MenuItem[] = [profileNavItem];
  if (profileNavItem.children) {
    items.push(...profileNavItem.children);
  }
  for (const section of menuConfig) {
    for (const item of section.items) {
      items.push(item);
      if (item.children) items.push(...item.children);
    }
  }
  return items;
}

const ALL_MENU_ITEMS = collectMenuItems();

/** Longest matching menu path wins (e.g. /ess/attendance/web → /ess/attendance parent). */
export function findMenuItemByPath(pathname: string): MenuItem | null {
  let best: MenuItem | null = null;
  let bestLen = 0;
  for (const item of ALL_MENU_ITEMS) {
    if (!item.path || !pathname.startsWith(item.path)) continue;
    if (item.path.length > bestLen) {
      best = item;
      bestLen = item.path.length;
    }
  }
  return best;
}

export function isPathAllowedForRoles(pathname: string, activeRoles: Set<Role>): boolean {
  const match = findMenuItemByPath(pathname);
  if (!match) return true;
  return match.allowedRoles.some((role) => activeRoles.has(role));
}
