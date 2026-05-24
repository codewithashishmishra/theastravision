'use client';

import React from 'react';
import { Card, CardBody } from "@nextui-org/react";
import { Search, UserCheck, Briefcase } from 'lucide-react';

export default function RecruitmentDashboard() {
  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">Talent Acquisition</h1>
        <p className="text-default-500 text-lg">Manage job pipelines, interviews, and candidate offers.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-primary/10 text-primary rounded-xl w-fit mb-4"><Briefcase size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Open Requisitions</h3>
            <p className="text-3xl font-bold text-foreground">8</p>
          </CardBody>
        </Card>
        
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-success/10 text-success rounded-xl w-fit mb-4"><UserCheck size={24} /></div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Candidates Offered</h3>
            <p className="text-3xl font-bold text-foreground">3</p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
