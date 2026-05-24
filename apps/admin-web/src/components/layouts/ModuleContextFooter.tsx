'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { getModuleContext } from '@/config/moduleContextMap';
import { Card, CardBody } from '@nextui-org/react';
import { Info, Link as LinkIcon, CheckCircle2 } from 'lucide-react';

export function ModuleContextFooter() {
  const pathname = usePathname();
  const context = getModuleContext(pathname);

  if (!pathname || pathname === '/' || pathname === '/login') return null;

  return (
    <Card className="mt-8 mb-6 border border-primary/20 bg-primary/5 shadow-sm">
      <CardBody className="p-5 md:p-6 flex flex-col md:flex-row gap-6">
        <div className="flex-1">
          <h4 className="text-primary font-bold text-lg flex items-center gap-2 mb-2">
            <Info size={20} /> {context.title} Context
          </h4>
          <p className="text-default-600 text-sm leading-relaxed">{context.purpose}</p>
        </div>
        
        <div className="flex-1 border-t md:border-t-0 md:border-l border-divider/50 pt-4 md:pt-0 md:pl-6">
          <h5 className="font-semibold text-sm flex items-center gap-2 mb-3 text-foreground">
            <CheckCircle2 size={16} className="text-success" /> Capabilities
          </h5>
          <ul className="text-sm text-default-500 space-y-1.5 list-disc pl-4">
            {context.capabilities.map((cap, i) => (
              <li key={i}>{cap}</li>
            ))}
          </ul>
        </div>

        <div className="flex-1 border-t md:border-t-0 md:border-l border-divider/50 pt-4 md:pt-0 md:pl-6">
          <h5 className="font-semibold text-sm flex items-center gap-2 mb-3 text-foreground">
            <LinkIcon size={16} className="text-secondary" /> Connected Modules
          </h5>
          <div className="flex flex-wrap gap-2">
            {context.dependencies.map((dep, i) => (
              <span key={i} className="px-2 py-1 bg-background border border-divider rounded-md text-xs font-medium text-default-600">
                {dep}
              </span>
            ))}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
