'use client';

import React from 'react';
import { Card, CardBody, Spinner } from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { dashboardsApi } from '@/lib/hrmsApi';

type DashboardProps = {
  role: 'hr' | 'manager' | 'company' | 'employee' | 'payroll' | 'finance' | 'it' | 'recruitment' | 'audit';
  title: string;
};

const fetchers = {
  hr: dashboardsApi.hr,
  manager: dashboardsApi.manager,
  company: dashboardsApi.company,
  employee: dashboardsApi.employee,
  payroll: dashboardsApi.payroll,
  finance: dashboardsApi.finance,
  it: dashboardsApi.it,
  recruitment: dashboardsApi.recruitment,
  audit: dashboardsApi.audit,
};

export function RoleDashboard({ role, title }: DashboardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', role],
    queryFn: async () => {
      const res = await fetchers[role]();
      return res.data as Record<string, number | string>;
    },
  });

  return (
    <div className="w-full flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">{title}</h1>
      {isLoading ? (
        <Spinner />
      ) : error ? (
        <p className="text-danger">Unable to load dashboard KPIs.</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(data ?? {}).map(([key, val]) => (
            <Card key={key} className="border border-divider">
              <CardBody>
                <p className="text-xs uppercase text-default-500">{key.replace(/_/g, ' ')}</p>
                <p className="text-3xl font-black text-primary">{String(val)}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
