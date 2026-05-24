'use client';

import React from 'react';
import { Card, CardBody, Progress, Button } from "@nextui-org/react";
import { Users, UserPlus, FileCheck2, Clock, CalendarDays, ArrowUpRight } from 'lucide-react';

export default function HRDashboard() {
  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">HR Operations Center</h1>
        <p className="text-default-500 text-lg">Manage your workforce, onboarding, and daily operations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-primary/10 text-primary rounded-xl">
                <Users size={24} />
              </div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Total Headcount</h3>
            <div className="flex items-end justify-between">
              <p className="text-3xl font-bold text-foreground">142</p>
              <p className="text-sm font-bold text-success flex items-center"><ArrowUpRight size={14}/> +3</p>
            </div>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-secondary/10 text-secondary rounded-xl">
                <UserPlus size={24} />
              </div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Active Onboardings</h3>
            <p className="text-3xl font-bold text-foreground">5</p>
            <Progress value={60} color="secondary" size="sm" className="mt-4" />
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-warning/10 text-warning-600 rounded-xl">
                <Clock size={24} />
              </div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Pending Regularizations</h3>
            <p className="text-3xl font-bold text-foreground">12</p>
            <p className="text-xs text-default-500 mt-2">Requires HR Approval</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-danger/10 text-danger rounded-xl">
                <FileCheck2 size={24} />
              </div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Offboarding Pipeline</h3>
            <p className="text-3xl font-bold text-foreground">2</p>
            <p className="text-xs text-default-500 mt-2">Clearance pending</p>
          </CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
        <Card className="shadow-sm border border-divider flex-1">
          <CardBody className="p-6">
            <h3 className="text-lg font-bold text-foreground mb-4">Recent Joiners</h3>
            <div className="flex flex-col gap-4">
              {[1,2,3].map((i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-default-50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center font-bold text-primary">N</div>
                    <div className="flex flex-col">
                      <span className="font-bold text-sm">New Hire {i}</span>
                      <span className="text-xs text-default-500">Engineering Dept</span>
                    </div>
                  </div>
                  <Button size="sm" variant="flat">View</Button>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
        
        <Card className="shadow-sm border border-divider flex-1">
          <CardBody className="p-6">
            <h3 className="text-lg font-bold text-foreground mb-4">Upcoming Work Anniversaries</h3>
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-4 p-4 border border-divider rounded-xl">
                <CalendarDays className="text-primary" size={32} />
                <div className="flex flex-col">
                  <span className="font-bold">Sarah Smith</span>
                  <span className="text-sm text-default-500">5 Years on May 28th</span>
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
