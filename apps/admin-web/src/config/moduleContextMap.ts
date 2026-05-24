export type ModuleContext = {
  title: string;
  purpose: string;
  capabilities: string[];
  dependencies: string[];
};

export const moduleContextMap: Record<string, ModuleContext> = {
  '/dashboards/platform': {
    title: 'Platform Analytics',
    purpose: 'Provides live hardware scaling telemetry and cross-tenant platform health metrics.',
    capabilities: ['Monitor CPU, RAM, and Storage load', 'Track active authentications by method', 'Identify bottleneck constraints'],
    dependencies: ['Audit Logs', 'Tenants']
  },
  '/tenants/provisioning': {
    title: 'Tenant Provisioning',
    purpose: 'Manages the creation and lifecycle of multi-tenant environments and client domains.',
    capabilities: ['Create new tenant workspaces', 'Disable or enable tenants', 'Configure tenant domains'],
    dependencies: ['Global Settings', 'Platform Audit Logs']
  },
  '/tenants/subscriptions': {
    title: 'Tenant Subscriptions',
    purpose: 'Tracks active tenant subscriptions, billing lifecycles, and platform quotas.',
    capabilities: ['View active subscriber details', 'Check subscription start dates'],
    dependencies: ['Tenant Provisioning', 'Finance Billing']
  },
  '/settings/flags': {
    title: 'Feature Flags',
    purpose: 'Dynamically toggle platform features and experimental functionality on the fly without code deployments.',
    capabilities: ['Enable/Disable beta features globally', 'Create new feature flag identifiers', 'Manage feature rollout phases'],
    dependencies: ['Platform Configuration']
  },
  '/dashboards/hr': {
    title: 'HR Operations',
    purpose: 'Centralized overview of human resources metrics, attendance, and employee movement.',
    capabilities: ['View live headcount', 'Track leave trends', 'Monitor onboarding progress'],
    dependencies: ['Employees', 'Leave Management', 'Attendance']
  }
};

export function getModuleContext(pathname: string): ModuleContext {
  if (moduleContextMap[pathname]) {
    return moduleContextMap[pathname];
  }
  
  // Fallback string generator
  const segments = pathname.split('/').filter(Boolean);
  const title = segments.length > 0 
    ? segments.map(s => s.charAt(0).toUpperCase() + s.slice(1).replace(/-/g, ' ')).join(' - ')
    : 'Module';

  return {
    title,
    purpose: `Operational management and administrative controls for the ${title} module.`,
    capabilities: ['View related records and statistics', 'Manage associated module configurations', 'Export or filter analytical data'],
    dependencies: ['Core Platform Services']
  };
}
