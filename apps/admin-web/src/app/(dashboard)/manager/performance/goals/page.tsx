'use client';

import React from 'react';
import { Card, CardBody, Progress, Avatar, Button, Chip } from '@nextui-org/react';
import { Target, TrendingUp, AlertTriangle, MessageSquare } from 'lucide-react';

const TEAM_GOALS = [
  { id: '1', emp: 'Sarah Smith', role: 'Frontend Dev', goal: 'Migrate to Next.js 14', progress: 85, status: 'On Track', avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026024d' },
  { id: '2', emp: 'Mike Johnson', role: 'Backend Dev', goal: 'Reduce API Latency by 50%', progress: 30, status: 'At Risk', avatar: 'https://i.pravatar.cc/150?u=1' },
  { id: '3', emp: 'Emily Chen', role: 'UX Designer', goal: 'Design System V2 Launch', progress: 100, status: 'Completed', avatar: 'https://i.pravatar.cc/150?u=2' },
];

export default function PerformanceGoalsPage() {
  return (
    <div className="w-full flex flex-col gap-6">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            Team Objectives & Key Results (OKRs)
          </h1>
          <p className="text-sm text-default-500 mt-1">
            Track and review your team's quarterly performance goals.
          </p>
        </div>
        <Button color="primary" className="font-bold shadow-lg" startContent={<Target size={18} />}>
          Assign New Goal
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6 flex flex-row items-center justify-between">
            <div>
              <p className="text-sm font-medium text-default-500">Avg. Completion Rate</p>
              <p className="text-3xl font-bold text-foreground mt-1">72%</p>
            </div>
            <div className="p-4 bg-primary/10 text-primary rounded-full"><TrendingUp size={24} /></div>
          </CardBody>
        </Card>
        
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6 flex flex-row items-center justify-between">
            <div>
              <p className="text-sm font-medium text-default-500">Goals At Risk</p>
              <p className="text-3xl font-bold text-danger mt-1">1</p>
            </div>
            <div className="p-4 bg-danger/10 text-danger rounded-full"><AlertTriangle size={24} /></div>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6 flex flex-row items-center justify-between">
            <div>
              <p className="text-sm font-medium text-default-500">Goals Completed</p>
              <p className="text-3xl font-bold text-success mt-1">1</p>
            </div>
            <div className="p-4 bg-success/10 text-success rounded-full"><Target size={24} /></div>
          </CardBody>
        </Card>
      </div>

      {/* Goal Cards */}
      <h3 className="text-lg font-bold mt-4">Active Goals (Q2 2026)</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {TEAM_GOALS.map((g) => (
          <Card key={g.id} className="shadow-sm border border-divider hover:shadow-md transition-shadow">
            <CardBody className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <Avatar src={g.avatar} className="ring-2 ring-primary/20" />
                  <div className="flex flex-col">
                    <span className="font-bold text-[15px]">{g.emp}</span>
                    <span className="text-xs text-default-500">{g.role}</span>
                  </div>
                </div>
                <Chip 
                  size="sm" 
                  variant="flat" 
                  color={g.status === 'Completed' ? 'success' : g.status === 'At Risk' ? 'danger' : 'primary'}
                  className="font-bold"
                >
                  {g.status}
                </Chip>
              </div>

              <div className="bg-default-50 p-4 rounded-xl border border-divider/50 mb-6">
                <h4 className="font-bold text-foreground mb-1">"{g.goal}"</h4>
                <p className="text-xs text-default-500">Weightage: 40% of Q2 Appraisal</p>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-sm font-bold">
                  <span>Progress</span>
                  <span>{g.progress}%</span>
                </div>
                <Progress 
                  value={g.progress} 
                  color={g.status === 'Completed' ? 'success' : g.status === 'At Risk' ? 'danger' : 'primary'} 
                  className="h-2"
                />
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-divider">
                <Button size="sm" variant="light" startContent={<MessageSquare size={16} />}>
                  Check-in
                </Button>
                <Button size="sm" color="primary" variant="flat">
                  Update Progress
                </Button>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

    </div>
  );
}
