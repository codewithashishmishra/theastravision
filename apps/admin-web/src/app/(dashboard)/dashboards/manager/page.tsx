'use client';

import React from 'react';
import { Card, CardBody, Button } from "@nextui-org/react";
import { Users, CheckCircle, Clock, Award } from 'lucide-react';

export default function ManagerDashboard() {
  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">My Team Dashboard</h1>
        <p className="text-default-500 text-lg">Oversee your direct reports, approvals, and team performance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-primary/10 text-primary rounded-xl w-fit mb-4"><Users size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Direct Reports</h3>
            <p className="text-3xl font-bold text-foreground">12</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-warning/10 text-warning-600 rounded-xl w-fit mb-4"><Clock size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Pending Approvals</h3>
            <p className="text-3xl font-bold text-foreground">4</p>
            <p className="text-xs text-warning-600 font-bold mt-2">Leaves & Expenses</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-success/10 text-success rounded-xl w-fit mb-4"><CheckCircle size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Team Attendance Today</h3>
            <p className="text-3xl font-bold text-foreground">11/12</p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
