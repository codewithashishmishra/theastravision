'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, Button, ButtonGroup, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from '@nextui-org/react';
import Link from 'next/link';
import { Activity, AlertTriangle, Clock, Server } from 'lucide-react';
import { auditApi } from '@/lib/auditApi';
import { MetricsCharts } from '@/components/audit/MetricsCharts';
import { ServiceStatusGrid } from '@/components/audit/ServiceStatusGrid';

export default function SystemAuditDashboard() {
  const [range, setRange] = useState('1h');
  const [metrics, setMetrics] = useState<any>(null);
  const [services, setServices] = useState<any[]>([]);
  const [errorLogs, setErrorLogs] = useState<any[]>([]);

  useEffect(() => {
    auditApi.platformMetrics(range).then((r) => setMetrics(r.data));
    auditApi.platformServices().then((r) => setServices(r.data.services || []));
    auditApi.systemLogs({ level: 'ERROR', since: '1 hour ago', limit: 50 }).then((r) => setErrorLogs(r.data.results || []));
  }, [range]);

  const summary = metrics?.summary;

  return (
    <div className="w-full flex flex-col gap-6 p-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-foreground">System Audit Dashboard</h1>
          <p className="text-default-500 text-lg">API health, latency, service status, and recent errors.</p>
        </div>
        <ButtonGroup>
          {['1h', '24h', '7d'].map((r) => (
            <Button key={r} size="sm" variant={range === r ? 'solid' : 'flat'} onPress={() => setRange(r)}>{r}</Button>
          ))}
        </ButtonGroup>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-divider shadow-sm">
          <CardBody className="p-5 flex gap-3">
            <AlertTriangle className="text-danger" />
            <div>
              <p className="text-sm text-default-500">Error rate</p>
              <p className="text-2xl font-bold">{summary?.error_rate_percent ?? 0}%</p>
            </div>
          </CardBody>
        </Card>
        <Card className="border border-divider shadow-sm">
          <CardBody className="p-5 flex gap-3">
            <Clock className="text-warning" />
            <div>
              <p className="text-sm text-default-500">P95 latency</p>
              <p className="text-2xl font-bold">{summary?.p95_latency_ms ?? 0} ms</p>
            </div>
          </CardBody>
        </Card>
        <Card className="border border-divider shadow-sm">
          <CardBody className="p-5 flex gap-3">
            <Activity className="text-primary" />
            <div>
              <p className="text-sm text-default-500">Requests</p>
              <p className="text-2xl font-bold">{summary?.total_requests ?? 0}</p>
            </div>
          </CardBody>
        </Card>
        <Card className="border border-divider shadow-sm">
          <CardBody className="p-5 flex gap-3">
            <Server className="text-secondary" />
            <div>
              <p className="text-sm text-default-500">Services up</p>
              <p className="text-2xl font-bold">
                {services.filter((s) => ['running', 'active'].includes(s.state)).length}/{services.length || '—'}
              </p>
            </div>
          </CardBody>
        </Card>
      </div>

      <Card className="border border-divider shadow-sm">
        <CardBody className="p-5">
          <MetricsCharts timeseries={metrics?.timeseries || []} byStatus={summary?.by_status} />
        </CardBody>
      </Card>

      <Card className="border border-divider shadow-sm">
        <CardBody className="p-5 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold">Service health</h2>
            <Button as={Link} href="/audit/system-logs" size="sm" variant="flat">Open log explorer</Button>
          </div>
          <ServiceStatusGrid services={services} />
        </CardBody>
      </Card>

      <Card className="border border-divider shadow-sm">
        <CardBody className="p-5 flex flex-col gap-4">
          <h2 className="text-lg font-bold">Top slow endpoints</h2>
          <Table removeWrapper aria-label="Slow endpoints">
            <TableHeader>
              <TableColumn>Endpoint</TableColumn>
              <TableColumn>Duration (ms)</TableColumn>
            </TableHeader>
            <TableBody emptyContent="No data yet.">
              {(metrics?.slow_endpoints || []).map((row: { endpoint: string; duration_ms: number }) => (
                <TableRow key={row.endpoint}>
                  <TableCell className="font-mono text-xs">{row.endpoint}</TableCell>
                  <TableCell>{row.duration_ms}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      <Card className="border border-divider shadow-sm">
        <CardBody className="p-5">
          <h2 className="text-lg font-bold mb-4">Recent errors</h2>
          <div className="font-mono text-xs max-h-48 overflow-y-auto space-y-1">
            {errorLogs.map((log, i) => (
              <div key={i} className="text-danger">{log.service}: {log.message}</div>
            ))}
            {!errorLogs.length && <p className="text-default-500">No recent ERROR lines.</p>}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
