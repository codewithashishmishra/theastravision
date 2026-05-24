'use client';

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts';

type TimeseriesPoint = {
  time: string;
  requests?: number;
  errors?: number;
  error_rate?: number;
  latency_avg?: number;
};

type Props = {
  timeseries: TimeseriesPoint[];
  byStatus?: Record<string, number>;
  showLatency?: boolean;
};

export function MetricsCharts({ timeseries, byStatus, showLatency = true }: Props) {
  const chartData = timeseries.map((p) => ({
    ...p,
    label: new Date(p.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }));

  const statusData = byStatus
    ? Object.entries(byStatus).map(([code, count]) => ({ code, count }))
    : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="h-64">
        <p className="text-sm font-medium text-default-500 mb-2">Requests & errors</p>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Area type="monotone" dataKey="requests" stackId="1" stroke="hsl(var(--nextui-primary))" fill="hsl(var(--nextui-primary))" fillOpacity={0.3} />
            <Area type="monotone" dataKey="errors" stackId="2" stroke="hsl(var(--nextui-danger))" fill="hsl(var(--nextui-danger))" fillOpacity={0.4} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      {showLatency && (
        <div className="h-64">
          <p className="text-sm font-medium text-default-500 mb-2">Avg latency (ms)</p>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="latency_avg" stroke="hsl(var(--nextui-warning))" fill="hsl(var(--nextui-warning))" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
      {statusData.length > 0 && (
        <div className="h-64 lg:col-span-2">
          <p className="text-sm font-medium text-default-500 mb-2">Status codes</p>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={statusData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="code" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="hsl(var(--nextui-secondary))" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
