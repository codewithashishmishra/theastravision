'use client';

import { ResourcePage } from '@/components/crud/ResourcePage';
import { resourcePageConfigs } from '@/config/resourcePageConfigs';

export default function Page() {
  const config = resourcePageConfigs['attendance-regularization'];
  if (!config) return <div className="p-8">Configuration missing.</div>;
  return <ResourcePage config={config} />;
}
