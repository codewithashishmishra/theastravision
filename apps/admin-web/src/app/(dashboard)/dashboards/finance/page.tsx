'use client';

import React from 'react';
import { Card, CardBody, Progress } from "@nextui-org/react";
import { PieChart, TrendingUp, AlertOctagon, RefreshCcw } from 'lucide-react';

export default function FinanceDashboard() {
  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">Finance & Accounting</h1>
        <p className="text-default-500 text-lg">Track expenses, settlements, and organizational cash flow.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-primary/10 text-primary rounded-xl w-fit mb-4"><PieChart size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Monthly Burn Rate</h3>
            <p className="text-3xl font-bold text-foreground">$245K</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-danger/10 text-danger rounded-xl w-fit mb-4"><AlertOctagon size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Pending Expense Claims</h3>
            <p className="text-3xl font-bold text-foreground">24</p>
            <p className="text-xs text-danger font-bold mt-2">$8,430 Unsettled</p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
