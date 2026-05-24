'use client';

import { ResourcePage } from '@/components/crud/ResourcePage';
import { resourcePageConfigs } from '@/config/resourcePageConfigs';

export default function Page() {
  return <ResourcePage config={resourcePageConfigs['payroll-declarations']} />;
}
