'use client';

import { ResourcePage } from '@/components/crud/ResourcePage';
import { resourcePageConfigs } from '@/config/resourcePageConfigs';

export default function LeavePoliciesPage() {
  return <ResourcePage config={resourcePageConfigs['leave-policies']} />;
}
