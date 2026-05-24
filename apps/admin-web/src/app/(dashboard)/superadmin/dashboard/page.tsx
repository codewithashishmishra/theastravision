'use client';

import React from 'react';
import { Card, CardBody, Progress, Button } from '@nextui-org/react';
import { Users, Activity, Flame, DollarSign, Plus, FileText, BellRing, Server, CreditCard } from 'lucide-react';
import { useTheme } from 'next-themes';

export default function Dashboard() {
  const { theme } = useTheme();

  return (
    <div className="flex flex-col gap-6 w-full pb-10">
      
      {/* Welcome Banner */}
      <Card 
        shadow="sm" 
        className="border border-divider w-full overflow-hidden relative bg-gradient-to-r from-content1 to-orange-50 dark:to-[#1a1311]"
      >
        <CardBody className="p-8 md:p-10 flex flex-col items-start z-10">
          <h1 className="text-3xl font-extrabold text-foreground tracking-tight mb-2">
            Welcome back, <span className="text-primary">Admin!</span>
          </h1>
          <p className="text-default-500 font-medium mb-8 max-w-lg">
            Your platform is looking vibrant today. Here's what's happening with your tenants and resources.
          </p>
          
          <div className="flex items-center gap-4">
            <Button color="primary" variant="bordered" className="font-semibold border-2" startContent={<Plus size={18} />}>
              Create New Tenant
            </Button>
            <Button variant="flat" className="font-semibold bg-default-100" startContent={<FileText size={18} />}>
              View Reports
            </Button>
          </div>
        </CardBody>
        
        {/* Soft decorative gradient blob on the right */}
        <div className="absolute -right-20 -top-20 w-96 h-96 bg-primary/20 blur-[100px] rounded-full pointer-events-none" />
      </Card>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Total Revenue', value: '$24,500', trend: '+12%', icon: DollarSign, color: 'text-orange-500' },
          { title: 'Active Tenants', value: '1,245', trend: '+5%', icon: Users, color: 'text-orange-500' },
          { title: 'New Signups', value: '342', trend: '+18%', icon: Flame, color: 'text-orange-500' },
          { title: 'Conversion Rate', value: '4.3%', trend: '-1%', trendNeg: true, icon: Activity, color: 'text-orange-500' },
        ].map((stat, idx) => (
          <Card key={idx} shadow="none" className="border border-divider bg-content1">
            <CardBody className="p-6 flex flex-col justify-between">
              <div className="flex justify-between items-start mb-2">
                <p className="text-sm font-semibold text-default-500">{stat.title}</p>
                <div className={`w-8 h-8 rounded-lg bg-default-100 flex items-center justify-center ${stat.color}`}>
                  <stat.icon size={16} />
                </div>
              </div>
              <h3 className="text-3xl font-bold text-foreground mb-4">{stat.value}</h3>
              <p className="text-xs font-medium text-default-500">
                <span className={stat.trendNeg ? 'text-danger' : 'text-success'}>{stat.trend}</span> vs last month
              </p>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Performance Overview (Chart placeholder) */}
        <Card shadow="none" className="lg:col-span-2 border border-divider bg-content1">
          <CardBody className="p-0">
            <div className="p-6 border-b border-divider flex items-center gap-2">
              <Activity size={18} className="text-primary" />
              <h3 className="text-md font-bold text-foreground">Performance Overview</h3>
            </div>
            <div className="p-6 h-72 flex flex-col justify-between">
              {/* Fake Chart Lines */}
              <div className="flex-1 border-b border-divider/50 w-full" />
              <div className="flex-1 border-b border-divider/50 w-full" />
              <div className="flex-1 border-b border-divider/50 w-full" />
              <div className="flex-1 border-b border-divider/50 w-full" />
              <div className="flex-1 w-full relative">
                {/* A mockup line graphic could go here */}
                <svg className="absolute bottom-0 left-0 w-full h-40" preserveAspectRatio="none" viewBox="0 0 100 100">
                  <path d="M0,100 L0,50 C20,40 30,70 50,40 C70,10 80,60 100,20 L100,100 Z" fill="url(#gradient)" opacity="0.2" />
                  <path d="M0,50 C20,40 30,70 50,40 C70,10 80,60 100,20" fill="none" stroke="currentColor" className="text-primary" strokeWidth="2" />
                  <defs>
                    <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="currentColor" className="text-primary" />
                      <stop offset="100%" stopColor="transparent" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Recent Activity */}
        <Card shadow="none" className="border border-divider bg-content1">
          <CardBody className="p-0">
            <div className="p-6 border-b border-divider flex items-center gap-2">
              <BellRing size={18} className="text-primary" />
              <h3 className="text-md font-bold text-foreground">Recent Activity</h3>
            </div>
            <div className="p-6 flex flex-col gap-6">
              
              <div className="flex gap-4 relative">
                <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />
                <div className="absolute left-1 top-4 bottom-[-16px] w-[1px] bg-divider" />
                <div>
                  <p className="text-sm font-bold text-foreground">New tenant registered</p>
                  <p className="text-xs font-medium text-default-400 mt-0.5">5 min ago</p>
                </div>
              </div>

              <div className="flex gap-4 relative">
                <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />
                <div className="absolute left-1 top-4 bottom-[-16px] w-[1px] bg-divider" />
                <div>
                  <p className="text-sm font-bold text-foreground">Server capacity updated</p>
                  <p className="text-xs font-medium text-default-400 mt-0.5">1 hour ago</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />
                <div>
                  <p className="text-sm font-bold text-foreground">Payment received</p>
                  <p className="text-xs font-medium text-default-400 mt-0.5">2 hours ago</p>
                </div>
              </div>

            </div>
          </CardBody>
        </Card>

      </div>
    </div>
  );
}
