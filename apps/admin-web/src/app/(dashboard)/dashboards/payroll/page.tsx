'use client';

import React from 'react';
import { Card, CardBody, Progress, Button } from "@nextui-org/react";
import { Wallet, DollarSign, FileCheck, Landmark } from 'lucide-react';

export default function PayrollDashboard() {
  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">Payroll Command Center</h1>
        <p className="text-default-500 text-lg">Manage salary disbursements and statutory compliances.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-success/10 text-success rounded-xl"><Wallet size={24} /></div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Total Payout (May)</h3>
            <p className="text-3xl font-bold text-foreground">$142,500</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-warning/10 text-warning-600 rounded-xl"><Landmark size={24} /></div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Pending Taxes (TDS/PF)</h3>
            <p className="text-3xl font-bold text-foreground">$32,100</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-primary/10 text-primary rounded-xl"><FileCheck size={24} /></div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Payslips Generated</h3>
            <p className="text-3xl font-bold text-foreground">103/142</p>
            <Progress value={75} color="primary" size="sm" className="mt-4" />
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
