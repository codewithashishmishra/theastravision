'use client';

import React from 'react';
import { Card, CardBody } from "@nextui-org/react";
import { Activity, ShieldAlert, BookOpen } from 'lucide-react';

export default function AuditDashboard() {
  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">Compliance & Audit</h1>
        <p className="text-default-500 text-lg">Monitor system logs, anomalies, and compliance metrics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-danger/10 text-danger rounded-xl w-fit mb-4"><ShieldAlert size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Critical Anomalies</h3>
            <p className="text-3xl font-bold text-foreground">0</p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
