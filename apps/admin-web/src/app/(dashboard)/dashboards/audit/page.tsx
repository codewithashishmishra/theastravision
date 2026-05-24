'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardBody, Button, Spinner } from '@nextui-org/react';
import Link from 'next/link';
import { ShieldAlert, BookOpen, Users, Globe } from 'lucide-react';
import { dashboardsApi } from '@/lib/hrmsApi';

export default function AuditDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardsApi.audit()
      .then((r) => setData(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex justify-center p-12"><Spinner /></div>;
  }

  const cards = [
    { label: 'Failed logins (24h)', value: data?.failed_logins_24h ?? 0, icon: ShieldAlert, color: 'text-danger' },
    { label: 'Admin actions (24h)', value: data?.admin_actions_24h ?? 0, icon: BookOpen, color: 'text-primary' },
    { label: 'Login sessions (24h)', value: data?.login_sessions_24h ?? 0, icon: Users, color: 'text-secondary' },
    { label: 'Unique IPs (24h)', value: data?.unique_ips_24h ?? 0, icon: Globe, color: 'text-warning' },
  ];

  return (
    <div className="w-full flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">Compliance & Audit</h1>
        <p className="text-default-500 text-lg">Monitor anomalies and compliance metrics for your tenant.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <Card key={label} className="shadow-sm border border-divider">
            <CardBody className="p-6">
              <div className={`p-3 bg-default-100 rounded-xl w-fit mb-4 ${color}`}><Icon size={24} /></div>
              <h3 className="text-default-500 text-sm font-medium mb-1">{label}</h3>
              <p className="text-3xl font-bold text-foreground">{value}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button as={Link} href="/audit/logins" color="primary" variant="flat">Login Logs</Button>
        <Button as={Link} href="/audit/admin" color="primary" variant="flat">Admin Action Audits</Button>
        <Button as={Link} href="/audit/payroll" variant="bordered">Compliance Reports</Button>
      </div>
    </div>
  );
}