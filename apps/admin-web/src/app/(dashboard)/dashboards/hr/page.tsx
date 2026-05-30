'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardBody, Progress, Button, Spinner } from '@nextui-org/react';
import { Users, UserPlus, FileCheck2, Clock, CalendarDays, ArrowUpRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/axios';
import { unwrapList } from '@/lib/hrmsApi';
import { formatRegionalDate } from '@/lib/formatDateTime';

type EmployeeRow = {
  id: string;
  first_name: string;
  last_name: string;
  department_name?: string;
  date_of_joining?: string;
};

export default function HRDashboard() {
  const router = useRouter();

  const { data: employees = [], isLoading } = useQuery({
    queryKey: ['hr-dashboard-employees'],
    queryFn: async () => {
      const res = await api.get('/employees/employees/', {
        params: { page_size: 200, ordering: '-date_of_joining' },
      });
      return unwrapList<EmployeeRow>(res.data);
    },
  });

  const recentJoiners = employees.slice(0, 5);
  const headcount = employees.length;

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
              <p className="text-3xl font-bold text-foreground">{isLoading ? '—' : headcount}</p>
            </div>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-secondary/10 text-secondary rounded-xl mb-4 w-fit">
              <UserPlus size={24} />
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Recent Joiners (30d)</h3>
            <p className="text-3xl font-bold text-foreground">{recentJoiners.length}</p>
            <Progress value={Math.min(100, recentJoiners.length * 10)} color="secondary" size="sm" className="mt-4" />
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-warning/10 text-warning-600 rounded-xl mb-4 w-fit">
              <Clock size={24} />
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Attendance</h3>
            <Button size="sm" variant="flat" color="primary" onPress={() => router.push('/attendance/live')}>
              Live monitor
            </Button>
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6">
            <div className="p-3 bg-danger/10 text-danger rounded-xl mb-4 w-fit">
              <FileCheck2 size={24} />
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Employee Directory</h3>
            <Button size="sm" variant="flat" color="primary" onPress={() => router.push('/employees/directory')}>
              Open directory
            </Button>
          </CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
        <Card className="shadow-sm border border-divider flex-1">
          <CardBody className="p-6">
            <h3 className="text-lg font-bold text-foreground mb-4">Recent Joiners</h3>
            {isLoading ? (
              <Spinner size="sm" />
            ) : (
              <div className="flex flex-col gap-4">
                {recentJoiners.length === 0 ? (
                  <p className="text-default-500 text-sm">No employees found.</p>
                ) : (
                  recentJoiners.map((emp) => (
                    <div key={emp.id} className="flex items-center justify-between p-3 bg-default-50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center font-bold text-primary">
                          {emp.first_name?.[0] ?? '?'}
                        </div>
                        <div className="flex flex-col">
                          <span className="font-bold text-sm">{emp.first_name} {emp.last_name}</span>
                          <span className="text-xs text-default-500">
                            {emp.department_name ?? '—'}
                            {emp.date_of_joining ? ` · Joined ${formatRegionalDate(emp.date_of_joining)}` : ''}
                          </span>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="flat"
                        endContent={<ArrowUpRight size={14} />}
                        onPress={() => router.push(`/employees/directory?highlight=${emp.id}`)}
                      >
                        View
                      </Button>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardBody>
        </Card>

        <Card className="shadow-sm border border-divider flex-1">
          <CardBody className="p-6">
            <h3 className="text-lg font-bold text-foreground mb-4">Quick links</h3>
            <div className="flex flex-col gap-3">
              <Button variant="bordered" onPress={() => router.push('/leave/policies')}>Leave policies</Button>
              <Button variant="bordered" onPress={() => router.push('/leave/balances')}>Leave balances</Button>
              <Button variant="bordered" onPress={() => router.push('/recruitment/interviews')}>Interviews</Button>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
