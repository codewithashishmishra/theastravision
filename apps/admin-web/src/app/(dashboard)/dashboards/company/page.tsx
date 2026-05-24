'use client';

import React from 'react';
import { Card, CardBody, Progress, Button } from "@nextui-org/react";
import { Users, Clock, CalendarDays, Wallet, TrendingUp, AlertTriangle } from 'lucide-react';

export default function CompanyDashboard() {
  return (
    <div className="w-full flex flex-col gap-6">
      
      {/* Welcome Header */}
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">Good Morning, Admin! 👋</h1>
        <p className="text-default-500 text-lg">Here's what's happening in your organization today.</p>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-primary/10 text-primary rounded-xl">
                <Users size={24} />
              </div>
              <span className="text-xs font-bold text-success flex items-center gap-1">
                <TrendingUp size={14} /> +12 this month
              </span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Total Active Employees</h3>
            <p className="text-3xl font-bold text-foreground">142</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-secondary/10 text-secondary rounded-xl">
                <Clock size={24} />
              </div>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Today's Attendance</h3>
            <div className="flex items-end justify-between">
              <p className="text-3xl font-bold text-foreground">92%</p>
              <p className="text-sm font-medium text-default-500">130/142 Present</p>
            </div>
            <Progress value={92} color="secondary" size="sm" className="mt-4" />
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-warning/10 text-warning-600 rounded-xl">
                <CalendarDays size={24} />
              </div>
              <span className="text-xs font-bold text-warning-600 bg-warning/20 px-2 py-1 rounded-full">
                Action Needed
              </span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Pending Leave Requests</h3>
            <p className="text-3xl font-bold text-foreground">8</p>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-success/10 text-success rounded-xl">
                <Wallet size={24} />
              </div>
              <span className="text-xs font-bold text-default-400">May 2026</span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Payroll Status</h3>
            <p className="text-2xl font-bold text-foreground mt-1 text-success flex items-center gap-2">
              Processing
            </p>
          </CardBody>
        </Card>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
        
        {/* Alerts / Action Items */}
        <Card className="shadow-sm border border-divider flex-1">
          <CardBody className="p-6">
            <h3 className="text-lg font-bold text-foreground flex items-center gap-2 mb-6">
              <AlertTriangle size={20} className="text-warning-500" /> Action Items
            </h3>
            
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between p-4 bg-default-100/50 rounded-xl">
                <div className="flex flex-col">
                  <span className="font-bold text-sm">Approve Pending Leaves</span>
                  <span className="text-xs text-default-500">8 requests waiting for manager approval</span>
                </div>
                <Button size="sm" color="primary" variant="flat">Review</Button>
              </div>

              <div className="flex items-center justify-between p-4 bg-danger/5 rounded-xl border border-danger/10">
                <div className="flex flex-col">
                  <span className="font-bold text-sm text-danger-600">Missing Attendance Logs</span>
                  <span className="text-xs text-default-500">12 employees forgot to clock out yesterday</span>
                </div>
                <Button size="sm" color="danger" variant="flat">Fix Now</Button>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* System Announcements */}
        <Card className="shadow-sm border border-divider bg-primary/5 flex-1">
          <CardBody className="p-8 text-center flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-4">
              <CalendarDays size={32} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-2">Upcoming Holiday</h3>
            <p className="text-default-500 mb-6">
              Memorial Day is approaching on Monday, May 25th. The office will be closed.
            </p>
            <Button color="primary" className="font-bold shadow-lg shadow-primary/30 w-full max-w-xs">
              View Holiday Calendar
            </Button>
          </CardBody>
        </Card>

      </div>
    </div>
  );
}
