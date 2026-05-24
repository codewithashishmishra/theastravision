'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardBody, Progress, Chip, Button } from "@nextui-org/react";
import Link from 'next/link';
import { Server, HardDrive, Cpu, Activity, Fingerprint, Lock, Mail, ScanFace, Database, AlertTriangle, Clock } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { api } from '@/lib/api';
import { auditApi } from '@/lib/auditApi';
import { ServiceStatusGrid } from '@/components/audit/ServiceStatusGrid';

const COLORS = {
  password: 'hsl(var(--nextui-primary))',
  totp: 'hsl(var(--nextui-warning))',
  passkey: 'hsl(var(--nextui-secondary))',
  face_scan: 'hsl(var(--nextui-success))'
};

export default function PlatformDashboard() {
  const [isClient, setIsClient] = useState(false);
  const [stats, setStats] = useState<any>(null);
  
  // Historical CPU data for the mini-chart
  const [cpuHistory, setCpuHistory] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);

  useEffect(() => {
    setIsClient(true);
    
    const fetchStats = async () => {
      try {
        const res = await api.get('/platform/monitoring/');
        setStats(res.data);
        
        setCpuHistory(prev => {
          const newHist = [...prev, { time: new Date().toLocaleTimeString(), cpu: res.data.system.cpu_usage_percent }];
          return newHist.slice(-20);
        });
      } catch (err) {
        console.error("Failed to fetch monitoring stats", err);
      }
    };

    auditApi.platformServices().then((r) => setServices(r.data.services || [])).catch(() => {});
    
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!isClient) return null;

  const cooldown = stats?.cooldown;
  const bothHigh =
    (stats?.system?.cpu_usage_percent ?? 0) >= (cooldown?.cpu_threshold ?? 80) &&
    (stats?.system?.ram_usage_percent ?? 0) >= (cooldown?.ram_threshold ?? 80);

  const authData = stats ? [
    { name: 'Password', value: stats.analytics.methods.password },
    { name: 'TOTP', value: stats.analytics.methods.totp },
    { name: 'Passkey', value: stats.analytics.methods.passkey },
    { name: 'Face Scan', value: stats.analytics.methods.face_scan },
  ] : [];

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2">
        <h1 className="text-3xl font-extrabold text-foreground">Platform Analytics & Monitoring</h1>
        <p className="text-default-500 text-lg">Live Super Admin view of multi-tenant scaling and hardware health.</p>
      </div>

      {cooldown?.cooldown_active && (
        <Card className="border-2 border-warning bg-warning/10">
          <CardBody className="p-4 flex flex-row items-center gap-4">
            <AlertTriangle className="text-warning shrink-0" size={28} />
            <div className="flex-1">
              <p className="font-bold text-warning">Platform cooldown active</p>
              <p className="text-sm text-default-600">
                Mutating API requests are paused. Saves resume in approximately{' '}
                {Math.ceil((cooldown.retry_after_seconds ?? 0) / 60)} minute(s).
                {cooldown.cooldown_until && (
                  <span className="block text-xs mt-1 opacity-80">Ends: {cooldown.cooldown_until}</span>
                )}
              </p>
            </div>
            <Chip color="warning" variant="flat">Cooling down</Chip>
          </CardBody>
        </Card>
      )}

      {!cooldown?.cooldown_active && (cooldown?.near_threshold || bothHigh) && (
        <Card className="border border-danger/30 bg-danger/5">
          <CardBody className="p-4 flex flex-row items-center gap-3 text-sm">
            <AlertTriangle className="text-danger shrink-0" size={22} />
            <span>
              CPU and RAM are near or at the {cooldown?.cpu_threshold ?? 80}% threshold. If both reach{' '}
              {cooldown?.cpu_threshold ?? 80}%, a 5-minute platform cooldown will start automatically.
            </span>
          </CardBody>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* CPU USAGE */}
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-danger/10 text-danger rounded-xl"><Cpu size={24} /></div>
              <span className="text-xs font-bold text-default-500">Live CPU</span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Total Processor Load</h3>
            <div className="flex items-end justify-between">
              <p className="text-3xl font-bold text-foreground">{stats?.system?.cpu_usage_percent || 0}%</p>
            </div>
            <Progress aria-label="CPU Usage" value={stats?.system?.cpu_usage_percent || 0} color={stats?.system?.cpu_usage_percent > 80 ? "danger" : "primary"} size="sm" className="mt-4" />
          </CardBody>
        </Card>

        {/* RAM USAGE */}
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-secondary/10 text-secondary rounded-xl"><Activity size={24} /></div>
              <span className="text-xs font-bold text-default-500">Live RAM</span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Memory Consumption</h3>
            <div className="flex items-end justify-between">
              <p className="text-3xl font-bold text-foreground">{stats?.system?.ram_usage_percent || 0}%</p>
              <p className="text-sm text-default-500">{stats?.system?.ram_used_gb || 0} GB / {stats?.system?.ram_total_gb || 0} GB</p>
            </div>
            <Progress
              aria-label="RAM Usage"
              value={stats?.system?.ram_usage_percent || 0}
              color={
                (stats?.system?.ram_usage_percent || 0) >= (cooldown?.ram_threshold ?? 80)
                  ? 'danger'
                  : 'secondary'
              }
              size="sm"
              className="mt-4"
            />
          </CardBody>
        </Card>

        {/* SYSTEM DISK */}
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-warning/10 text-warning-600 rounded-xl"><HardDrive size={24} /></div>
              <span className="text-xs font-bold text-default-500">OS Storage</span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Root Disk Space</h3>
            <div className="flex items-end justify-between">
              <p className="text-3xl font-bold text-foreground">{stats?.system?.disk_usage_percent || 0}%</p>
              <p className="text-sm text-default-500">{stats?.system?.disk_used_gb || 0} GB / {stats?.system?.disk_total_gb || 0} GB</p>
            </div>
            <Progress aria-label="Disk Usage" value={stats?.system?.disk_usage_percent || 0} color="warning" size="sm" className="mt-4" />
          </CardBody>
        </Card>

        {/* DB SIZE */}
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-success/10 text-success rounded-xl"><Database size={24} /></div>
              <span className="text-xs font-bold text-default-500">PostgreSQL</span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Database Allocation</h3>
            <p className="text-3xl font-bold text-foreground">{stats?.database?.size_mb || 0} <span className="text-lg">MB</span></p>
            <p className="text-sm text-default-500 mt-2">Active database clusters</p>
          </CardBody>
        </Card>

      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-danger/10 text-danger rounded-xl"><AlertTriangle size={24} /></div>
              <span className="text-xs font-bold text-default-500">API 1h</span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Error Rate</h3>
            <p className="text-3xl font-bold text-foreground">{stats?.api_metrics?.error_rate_percent ?? 0}%</p>
          </CardBody>
        </Card>
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-warning/10 text-warning rounded-xl"><Clock size={24} /></div>
              <span className="text-xs font-bold text-default-500">P95</span>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">API Latency</h3>
            <p className="text-3xl font-bold text-foreground">{stats?.api_metrics?.p95_latency_ms ?? 0} <span className="text-lg">ms</span></p>
          </CardBody>
        </Card>
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-primary/10 text-primary rounded-xl"><Activity size={24} /></div>
              <Button as={Link} href="/dashboards/system-audit" size="sm" variant="flat">Details</Button>
            </div>
            <h3 className="text-default-500 text-sm font-medium mb-1">Requests (1h)</h3>
            <p className="text-3xl font-bold text-foreground">{stats?.api_metrics?.total_requests_1h ?? 0}</p>
          </CardBody>
        </Card>
      </div>

      {services.length > 0 && (
        <Card className="shadow-sm border border-divider">
          <CardBody className="p-6 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold">Service status</h3>
              <Button as={Link} href="/audit/system-logs" size="sm" variant="flat">View logs</Button>
            </div>
            <ServiceStatusGrid services={services} />
          </CardBody>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4">
        
        {/* CPU CHART */}
        <Card className="col-span-2 shadow-sm border border-divider">
          <CardBody className="p-6">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-6">
              <Server className="text-primary" size={20}/> Hardware CPU Load History (Live)
            </h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%" minHeight={1}>
                <AreaChart data={cpuHistory} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--nextui-danger))" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="hsl(var(--nextui-danger))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--nextui-divider))" />
                  <XAxis dataKey="time" stroke="hsl(var(--nextui-default-500))" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} stroke="hsl(var(--nextui-default-500))" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'hsl(var(--nextui-content1))', borderColor: 'hsl(var(--nextui-divider))', borderRadius: '12px' }}
                    itemStyle={{ color: 'hsl(var(--nextui-foreground))' }}
                  />
                  <Area type="monotone" isAnimationActive={false} dataKey="cpu" stroke="hsl(var(--nextui-danger))" strokeWidth={3} fillOpacity={1} fill="url(#colorCpu)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>

        {/* AUTH ANALYTICS */}
        <Card className="col-span-1 shadow-sm border border-divider">
          <CardBody className="p-6 flex flex-col">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-6">
              <Lock className="text-secondary" size={20}/> Today's Logins ({stats?.analytics?.daily_visits_today || 0})
            </h3>
            
            <div className="h-48 w-full relative mb-4">
              <ResponsiveContainer width="100%" height="100%" minHeight={1}>
                <PieChart>
                  <Pie
                    data={authData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {authData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={Object.values(COLORS)[index]} />
                    ))}
                  </Pie>
                  <Tooltip 
                      contentStyle={{ backgroundColor: 'hsl(var(--nextui-content1))', borderColor: 'hsl(var(--nextui-divider))', borderRadius: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none flex-col">
                <span className="text-3xl font-bold">{stats?.analytics?.daily_visits_today || 0}</span>
                <span className="text-xs text-default-500">Sessions</span>
              </div>
            </div>

            <div className="flex flex-col gap-3 mt-auto">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium"><Mail size={16} className="text-primary"/> Password</div>
                <span className="font-bold">{stats?.analytics?.methods?.password || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium"><Lock size={16} className="text-warning"/> TOTP (2FA)</div>
                <span className="font-bold">{stats?.analytics?.methods?.totp || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium"><Fingerprint size={16} className="text-secondary"/> Passkeys</div>
                <span className="font-bold">{stats?.analytics?.methods?.passkey || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium"><ScanFace size={16} className="text-success"/> Face Scans</div>
                <span className="font-bold">{stats?.analytics?.methods?.face_scan || 0}</span>
              </div>
            </div>

          </CardBody>
        </Card>
      </div>
    </div>
  );
}
