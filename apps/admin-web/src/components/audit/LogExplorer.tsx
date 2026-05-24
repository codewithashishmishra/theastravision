'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button, Chip, Input, Select, SelectItem, Switch, Spinner,
} from '@nextui-org/react';
import { Search, RefreshCw } from 'lucide-react';
import ExportButton from '@/components/wfh/ExportButton';
import { TenantFilterSelect } from '@/components/audit/TenantFilterSelect';
import { auditApi, type SystemLogEntry } from '@/lib/auditApi';
import { formatUtcDateTime } from '@/lib/formatDateTime';

const LEVEL_COLORS: Record<string, 'default' | 'primary' | 'warning' | 'danger' | 'success'> = {
  DEBUG: 'default',
  INFO: 'primary',
  WARN: 'warning',
  WARNING: 'warning',
  ERROR: 'danger',
  CRITICAL: 'danger',
  FATAL: 'danger',
};

const SINCE_OPTIONS = [
  { key: '15m', label: '15 minutes', value: '15 min ago' },
  { key: '1h', label: '1 hour', value: '1 hour ago' },
  { key: '6h', label: '6 hours', value: '6 hours ago' },
  { key: '24h', label: '24 hours', value: '24 hours ago' },
];

type Props = {
  defaultService?: string;
};

export function LogExplorer({ defaultService }: Props) {
  const [service, setService] = useState(defaultService || '');
  const [sinceKey, setSinceKey] = useState('1h');
  const [level, setLevel] = useState('');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [liveTail, setLiveTail] = useState(false);
  const [logs, setLogs] = useState<SystemLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [tenantId, setTenantId] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const since = SINCE_OPTIONS.find((o) => o.key === sinceKey)?.value;

  const load = useCallback(() => {
    setLoading(true);
    auditApi.systemLogs({
      service: service || undefined,
      since,
      level: level || undefined,
      search: debouncedSearch || undefined,
      limit: 100,
      tenant_id: tenantId || undefined,
    })
      .then((res) => setLogs(res.data.results))
      .finally(() => setLoading(false));
  }, [service, since, level, debouncedSearch, tenantId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!liveTail) return undefined;
    const tick = () => {
      if (typeof document !== 'undefined' && document.hidden) return;
      load();
    };
    tick();
    const interval = setInterval(tick, 10_000);
    const onVisibility = () => {
      if (!document.hidden) load();
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [liveTail, load]);

  const exportRows = useMemo(
    () => logs.map((l) => ({ Time: l.timestamp, Level: l.level, Service: l.service, Message: l.message })),
    [logs],
  );

  return (
    <div className="w-full flex flex-col gap-4 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-extrabold text-foreground">System Log Explorer</h1>
        <p className="text-default-500">Tenant-filtered logs from ClickHouse, or Docker/journalctl stream when no tenant is selected.</p>
      </div>

      <div className="flex flex-wrap gap-3 items-end">
        <TenantFilterSelect value={tenantId} onChange={setTenantId} />
        <Select
          className="max-w-xs"
          label="Service"
          selectedKeys={service ? [service] : []}
          onSelectionChange={(keys) => setService(Array.from(keys)[0] as string || '')}
        >
          {['api', 'celery-worker', 'celery-beat', 'ai-service', 'admin-web'].map((s) => (
            <SelectItem key={s}>{s}</SelectItem>
          ))}
        </Select>
        <Select
          className="max-w-xs"
          label="Time range"
          selectedKeys={[sinceKey]}
          onSelectionChange={(keys) => setSinceKey(Array.from(keys)[0] as string)}
        >
          {SINCE_OPTIONS.map((o) => (
            <SelectItem key={o.key}>{o.label}</SelectItem>
          ))}
        </Select>
        <Select
          className="max-w-xs"
          label="Level"
          selectedKeys={level ? [level] : []}
          onSelectionChange={(keys) => setLevel(Array.from(keys)[0] as string || '')}
        >
          {['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'].map((l) => (
            <SelectItem key={l}>{l}</SelectItem>
          ))}
        </Select>
        <Input
          className="max-w-sm"
          placeholder="Search logs..."
          startContent={<Search size={16} />}
          value={search}
          onValueChange={setSearch}
        />
        <Switch isSelected={liveTail} onValueChange={setLiveTail}>Live tail</Switch>
        <Button isIconOnly variant="flat" onPress={load}><RefreshCw size={18} /></Button>
        <ExportButton data={exportRows} filename="system-logs" />
        <ExportButton data={exportRows} filename="system-logs" format="json" />
      </div>

      <div className="border border-divider rounded-xl overflow-hidden bg-default-50/50 min-h-[400px]">
        {loading && !logs.length ? (
          <div className="flex justify-center p-12"><Spinner /></div>
        ) : (
          <div className="font-mono text-xs divide-y divide-divider max-h-[70vh] overflow-y-auto">
            {logs.map((log, idx) => (
              <div key={`${log.timestamp}-${idx}`} className="hover:bg-default-100/80">
                <button
                  type="button"
                  className="w-full text-left px-4 py-2 flex gap-3 items-start"
                  onClick={() => setExpanded((p) => ({ ...p, [idx]: !p[idx] }))}
                >
                  <span className="text-default-400 shrink-0 w-44">{formatUtcDateTime(log.timestamp)}</span>
                  <Chip size="sm" color={LEVEL_COLORS[log.level] || 'default'} variant="flat" className="shrink-0">{log.level}</Chip>
                  <Chip size="sm" variant="bordered" className="shrink-0">{log.service}</Chip>
                  <span className="text-foreground break-all">{log.message}</span>
                </button>
                {expanded[idx] && (
                  <pre className="px-4 pb-3 text-default-500 whitespace-pre-wrap">{log.raw}</pre>
                )}
              </div>
            ))}
            {!logs.length && !loading && (
              <p className="p-8 text-center text-default-500">No logs found for the current filters.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
