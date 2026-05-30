'use client';

import React, { useEffect, useState } from 'react';
import {
  Card,
  CardBody,
  Button,
  Input,
  Switch,
  Spinner,
  Tabs,
  Tab,
  Textarea,
} from '@nextui-org/react';
import api from '@/lib/axios';
import { setFrontendDebugEnabled } from '@/lib/debugLogStore';
import { platformHealthApi } from '@/lib/hrmsApi';
import { useAuth } from '@/lib/AuthProvider';

const MODULE_UTIL = 'PLATFORM_UTILIZATION';
const MODULE_SMTP = 'SMTP';
const MODULE_AI = 'AI';
const MODULE_IMAP = 'IMAP';
const MODULE_DEBUG = 'FRONTEND_DEBUG';

type UtilizationConfig = {
  enabled: boolean;
  cpu_threshold_percent: number;
  ram_threshold_percent: number;
  cooldown_duration_seconds: number;
  sample_interval_seconds: number;
  super_admin_bypass: boolean;
  cooldown_message: string;
};

type SmtpConfig = {
  host: string;
  port: number;
  use_tls: boolean;
  use_ssl: boolean;
  ssl_verify: boolean;
  user: string;
  password: string;
  from_email: string;
  from_name: string;
  rate_per_minute: number;
};

type AiConfig = {
  provider: string;
  api_key: string;
  model: string;
};

type ImapConfig = {
  host: string;
  port: number;
  use_ssl: boolean;
  ssl_verify: boolean;
  user: string;
  password: string;
  folder: string;
  poll_interval_minutes: number;
};

type DebugConfig = {
  enabled: boolean;
};

type EnvConfigRow<T> = {
  id: string;
  module: string;
  decrypted_config: T;
};

const UTIL_DEFAULTS: UtilizationConfig = {
  enabled: true,
  cpu_threshold_percent: 80,
  ram_threshold_percent: 80,
  cooldown_duration_seconds: 300,
  sample_interval_seconds: 30,
  super_admin_bypass: false,
  cooldown_message:
    'System is cooling down. Please retry in about 5 minutes. Your changes are saved locally and will sync when the system is back.',
};

const SMTP_DEFAULTS: SmtpConfig = {
  host: 'p3plzcpnl506724.prod.phx3.secureserver.net',
  port: 465,
  use_tls: false,
  use_ssl: true,
  ssl_verify: true,
  user: 'notifications@theastravision.com',
  password: '',
  from_email: 'notifications@theastravision.com',
  from_name: 'The Astra Vision',
  rate_per_minute: 30,
};

const AI_DEFAULTS: AiConfig = {
  provider: 'openai',
  api_key: '',
  model: 'gpt-4o-mini',
};

const IMAP_DEFAULTS: ImapConfig = {
  host: 'p3plzcpnl506724.prod.phx3.secureserver.net',
  port: 993,
  use_ssl: true,
  ssl_verify: true,
  user: 'notifications@theastravision.com',
  password: '',
  folder: 'INBOX',
  poll_interval_minutes: 5,
};

const DEBUG_DEFAULTS: DebugConfig = {
  enabled: false,
};

type ModuleHealth = {
  module: string;
  status: string;
  latency_ms: number;
  message: string;
};

const HEALTH_STATUS_COLOR: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
  healthy: 'success',
  degraded: 'warning',
  down: 'danger',
  skipped: 'default',
};

async function loadModule<T>(module: string, defaults: T): Promise<{ id: string | null; form: T }> {
  try {
    const res = await api.get<EnvConfigRow<T>>(`/env-configs/${module}/`);
    const merged = { ...defaults, ...res.data.decrypted_config };
    if (module === MODULE_SMTP && (merged as SmtpConfig).password) {
      (merged as SmtpConfig).password = '********';
    }
    if (module === MODULE_AI && (merged as AiConfig).api_key) {
      (merged as AiConfig).api_key = '********';
    }
    if (module === MODULE_IMAP && (merged as ImapConfig).password) {
      (merged as ImapConfig).password = '********';
    }
    return { id: res.data.id, form: merged };
  } catch {
    return { id: null, form: defaults };
  }
}

async function saveModule<T extends Record<string, unknown>>(
  module: string,
  configId: string | null,
  form: T,
  secretKeys: string[] = [],
): Promise<void> {
  const payload: Record<string, unknown> = { ...form };
  for (const key of secretKeys) {
    if (payload[key] === '********') {
      delete payload[key];
    }
  }
  const body = { module, config: payload };
  if (configId) {
    await api.patch(`/env-configs/${module}/`, body);
  } else {
    await api.post('/env-configs/', body);
  }
}

export default function PlatformConfigPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [testSmtpLoading, setTestSmtpLoading] = useState(false);
  const [testImapLoading, setTestImapLoading] = useState(false);
  const [testToEmail, setTestToEmail] = useState('');
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthModules, setHealthModules] = useState<ModuleHealth[]>([]);
  const [simulateLoading, setSimulateLoading] = useState(false);

  const [utilId, setUtilId] = useState<string | null>(null);
  const [utilForm, setUtilForm] = useState<UtilizationConfig>(UTIL_DEFAULTS);

  const [smtpId, setSmtpId] = useState<string | null>(null);
  const [smtpForm, setSmtpForm] = useState<SmtpConfig>(SMTP_DEFAULTS);

  const [aiId, setAiId] = useState<string | null>(null);
  const [aiForm, setAiForm] = useState<AiConfig>(AI_DEFAULTS);

  const [imapId, setImapId] = useState<string | null>(null);
  const [imapForm, setImapForm] = useState<ImapConfig>(IMAP_DEFAULTS);

  const [debugId, setDebugId] = useState<string | null>(null);
  const [debugForm, setDebugForm] = useState<DebugConfig>(DEBUG_DEFAULTS);

  const [envFiles, setEnvFiles] = useState<{ api: string; ai_service: string }>({ api: '', ai_service: '' });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [util, smtp, ai, imap, debug, envRes] = await Promise.all([
        loadModule(MODULE_UTIL, UTIL_DEFAULTS),
        loadModule(MODULE_SMTP, SMTP_DEFAULTS),
        loadModule(MODULE_AI, AI_DEFAULTS),
        loadModule(MODULE_IMAP, IMAP_DEFAULTS),
        loadModule(MODULE_DEBUG, DEBUG_DEFAULTS),
        api.get('/config/env-file/').catch(() => ({ data: { api: '', ai_service: '' } })),
      ]);
      if (cancelled) return;
      setUtilId(util.id);
      setUtilForm(util.form);
      setSmtpId(smtp.id);
      setSmtpForm(smtp.form);
      setAiId(ai.id);
      setAiForm(ai.form);
      setImapId(imap.id);
      setImapForm(imap.form);
      setDebugId(debug.id);
      setDebugForm(debug.form);
      setFrontendDebugEnabled(debug.form.enabled);
      setEnvFiles(envRes.data);
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSaveUtil = async () => {
    setSaving(true);
    setMessage('');
    try {
      await saveModule(MODULE_UTIL, utilId, utilForm);
      if (!utilId) {
        const res = await api.get<EnvConfigRow<UtilizationConfig>>(`/env-configs/${MODULE_UTIL}/`);
        setUtilId(res.data.id);
      }
      setMessage('Utilization settings saved.');
    } catch {
      setMessage('Failed to save utilization settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveSmtp = async () => {
    setSaving(true);
    setMessage('');
    try {
      await saveModule(MODULE_SMTP, smtpId, smtpForm, ['password']);
      if (!smtpId) {
        const res = await api.get<EnvConfigRow<SmtpConfig>>(`/env-configs/${MODULE_SMTP}/`);
        setSmtpId(res.data.id);
        setSmtpForm({ ...smtpForm, password: res.data.decrypted_config.password ? '********' : '' });
      }
      setMessage('SMTP settings saved (encrypted at rest).');
    } catch {
      setMessage('Failed to save SMTP settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAi = async () => {
    setSaving(true);
    setMessage('');
    try {
      await saveModule(MODULE_AI, aiId, aiForm, ['api_key']);
      if (!aiId) {
        const res = await api.get<EnvConfigRow<AiConfig>>(`/env-configs/${MODULE_AI}/`);
        setAiId(res.data.id);
        setAiForm({ ...aiForm, api_key: res.data.decrypted_config.api_key ? '********' : '' });
      }
      setMessage('AI settings saved.');
    } catch {
      setMessage('Failed to save AI settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveImap = async () => {
    setSaving(true);
    setMessage('');
    try {
      await saveModule(MODULE_IMAP, imapId, imapForm, ['password']);
      if (!imapId) {
        const res = await api.get<EnvConfigRow<ImapConfig>>(`/env-configs/${MODULE_IMAP}/`);
        setImapId(res.data.id);
        setImapForm({
          ...imapForm,
          password: res.data.decrypted_config.password ? '********' : '',
        });
      }
      setMessage('IMAP settings saved (encrypted at rest).');
    } catch {
      setMessage('Failed to save IMAP settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveEnvFiles = async () => {
    setSaving(true);
    setMessage('');
    try {
      await api.post('/config/env-file/', envFiles);
      setMessage('System environment files saved. A server restart may be required.');
    } catch {
      setMessage('Failed to save environment files.');
    } finally {
      setSaving(false);
    }
  };

  const handleTestSmtp = async () => {
    const to = testToEmail || user?.email;
    if (!to) {
      setMessage('Enter a test recipient email or sign in with an email address.');
      return;
    }
    setTestSmtpLoading(true);
    setMessage('');
    try {
      const res = await platformHealthApi.testSmtp(to);
      setMessage(res.data.ok ? res.data.detail : `SMTP test failed: ${res.data.detail}`);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'SMTP test request failed.';
      setMessage(detail);
    } finally {
      setTestSmtpLoading(false);
    }
  };

  const handleTestImap = async () => {
    setTestImapLoading(true);
    setMessage('');
    try {
      const res = await platformHealthApi.testImap();
      const extra =
        res.data.mailbox_count != null ? ` (${res.data.mailbox_count} messages)` : '';
      setMessage(res.data.ok ? `${res.data.detail}${extra}` : `IMAP test failed: ${res.data.detail}`);
    } catch {
      setMessage('IMAP test request failed.');
    } finally {
      setTestImapLoading(false);
    }
  };

  const loadHealth = async () => {
    setHealthLoading(true);
    try {
      const res = await platformHealthApi.modules();
      setHealthModules(res.data);
    } catch {
      setMessage('Failed to load module health.');
    } finally {
      setHealthLoading(false);
    }
  };

  const handleSimulateImapPoll = async () => {
    setSimulateLoading(true);
    setMessage('');
    try {
      const res = await platformHealthApi.simulateImapPoll();
      setMessage(`IMAP poll completed: ${JSON.stringify(res.data.result ?? res.data)}`);
    } catch {
      setMessage('IMAP poll simulation failed.');
    } finally {
      setSimulateLoading(false);
    }
  };

  const handleSaveDebug = async () => {
    setSaving(true);
    setMessage('');
    try {
      await saveModule(MODULE_DEBUG, debugId, debugForm);
      if (!debugId) {
        const res = await api.get<EnvConfigRow<DebugConfig>>(`/env-configs/${MODULE_DEBUG}/`);
        setDebugId(res.data.id);
      }
      setFrontendDebugEnabled(debugForm.enabled);
      setMessage('Debug settings saved.');
    } catch {
      setMessage('Failed to save debug settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="w-full max-w-3xl flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-extrabold text-foreground">Platform Config</h1>
        <p className="text-default-500 mt-1">
          Super Admin platform settings. SMTP credentials are encrypted. Set{' '}
          <code className="text-xs bg-default-100 px-1 rounded">PUBLIC_API_BASE_URL</code> on the API
          server so email open-tracking pixels resolve correctly in production.
        </p>
      </div>

      <Tabs aria-label="Platform config sections">
        <Tab key="util" title="Utilization">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-5 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold">Enable utilization cooldown</p>
                  <p className="text-xs text-default-500">Module: {MODULE_UTIL}</p>
                </div>
                <Switch
                  isSelected={utilForm.enabled}
                  onValueChange={(v) => setUtilForm((p) => ({ ...p, enabled: v }))}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  type="number"
                  label="CPU threshold (%)"
                  value={String(utilForm.cpu_threshold_percent)}
                  onValueChange={(v) =>
                    setUtilForm((p) => ({ ...p, cpu_threshold_percent: Number(v) || 0 }))
                  }
                />
                <Input
                  type="number"
                  label="RAM threshold (%)"
                  value={String(utilForm.ram_threshold_percent)}
                  onValueChange={(v) =>
                    setUtilForm((p) => ({ ...p, ram_threshold_percent: Number(v) || 0 }))
                  }
                />
                <Input
                  type="number"
                  label="Cooldown duration (seconds)"
                  value={String(utilForm.cooldown_duration_seconds)}
                  onValueChange={(v) =>
                    setUtilForm((p) => ({ ...p, cooldown_duration_seconds: Number(v) || 0 }))
                  }
                />
                <Input
                  type="number"
                  label="Sample interval (seconds)"
                  value={String(utilForm.sample_interval_seconds)}
                  onValueChange={(v) =>
                    setUtilForm((p) => ({ ...p, sample_interval_seconds: Number(v) || 0 }))
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <p className="font-semibold">Super Admin bypass</p>
                <Switch
                  isSelected={utilForm.super_admin_bypass}
                  onValueChange={(v) => setUtilForm((p) => ({ ...p, super_admin_bypass: v }))}
                />
              </div>
              <Input
                label="Cooldown user message"
                value={utilForm.cooldown_message}
                onValueChange={(v) => setUtilForm((p) => ({ ...p, cooldown_message: v }))}
              />
              <Button color="primary" isLoading={saving} onPress={handleSaveUtil}>
                Save utilization
              </Button>
            </CardBody>
          </Card>
        </Tab>

        <Tab key="smtp" title="SMTP (Cold Email)">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-4 p-6">
              <p className="text-sm text-default-500">
                cPanel SSL/TLS: host <strong>p3plzcpnl506724.prod.phx3.secureserver.net</strong>,
                port <strong>465</strong> with SSL (not STARTTLS on 587).
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="SMTP host"
                  value={smtpForm.host}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, host: v }))}
                />
                <Input
                  type="number"
                  label="Port"
                  value={String(smtpForm.port)}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, port: Number(v) || 587 }))}
                />
                <Input
                  label="Username"
                  value={smtpForm.user}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, user: v }))}
                />
                <Input
                  type="password"
                  label="Password"
                  placeholder="Leave blank to keep current"
                  value={smtpForm.password === '********' ? '' : smtpForm.password}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, password: v || '********' }))}
                />
                <Input
                  label="From email"
                  value={smtpForm.from_email}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, from_email: v }))}
                />
                <Input
                  label="From name"
                  value={smtpForm.from_name}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, from_name: v }))}
                />
                <Input
                  type="number"
                  label="Send rate (emails / minute)"
                  value={String(smtpForm.rate_per_minute)}
                  onValueChange={(v) =>
                    setSmtpForm((p) => ({ ...p, rate_per_minute: Number(v) || 30 }))
                  }
                />
              </div>
              <div className="flex gap-6">
                <Switch
                  isSelected={smtpForm.use_tls}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, use_tls: v, use_ssl: v ? false : p.use_ssl }))}
                >
                  Use TLS (STARTTLS)
                </Switch>
                <Switch
                  isSelected={smtpForm.use_ssl}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, use_ssl: v, use_tls: v ? false : p.use_tls }))}
                >
                  Use SSL
                </Switch>
                <Switch
                  isSelected={smtpForm.ssl_verify}
                  onValueChange={(v) => setSmtpForm((p) => ({ ...p, ssl_verify: v }))}
                >
                  Verify TLS certificate
                </Switch>
              </div>
              <p className="text-xs text-default-500">
                Disable certificate verification only for local mail or if antivirus intercepts
                SMTP TLS (not recommended for production).
              </p>
              <Input
                label="Test recipient email"
                placeholder={user?.email || 'you@company.com'}
                value={testToEmail}
                onValueChange={setTestToEmail}
              />
              <div className="flex flex-wrap gap-3">
                <Button color="primary" isLoading={saving} onPress={handleSaveSmtp}>
                  Save SMTP
                </Button>
                <Button variant="bordered" isLoading={testSmtpLoading} onPress={handleTestSmtp}>
                  Test SMTP
                </Button>
              </div>
            </CardBody>
          </Card>
        </Tab>

        <Tab key="imap" title="IMAP (Replies)">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-4 p-6">
              <p className="text-sm text-default-500">
                Inbound mailbox for cold campaign reply detection. Celery polls every 5 minutes.
                cPanel: same host as SMTP, port <strong>993</strong> IMAP over SSL.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="IMAP host"
                  value={imapForm.host}
                  onValueChange={(v) => setImapForm((p) => ({ ...p, host: v }))}
                />
                <Input
                  type="number"
                  label="Port"
                  value={String(imapForm.port)}
                  onValueChange={(v) => setImapForm((p) => ({ ...p, port: Number(v) || 993 }))}
                />
                <Input
                  label="Username"
                  value={imapForm.user}
                  onValueChange={(v) => setImapForm((p) => ({ ...p, user: v }))}
                />
                <Input
                  type="password"
                  label="Password"
                  placeholder="Leave blank to keep current"
                  value={imapForm.password === '********' ? '' : imapForm.password}
                  onValueChange={(v) => setImapForm((p) => ({ ...p, password: v || '********' }))}
                />
                <Input
                  label="Folder"
                  value={imapForm.folder}
                  onValueChange={(v) => setImapForm((p) => ({ ...p, folder: v }))}
                />
              </div>
              <div className="flex flex-wrap gap-6">
                <Switch
                  isSelected={imapForm.use_ssl}
                  onValueChange={(v) => setImapForm((p) => ({ ...p, use_ssl: v }))}
                >
                  Use SSL
                </Switch>
                <Switch
                  isSelected={imapForm.ssl_verify}
                  onValueChange={(v) => setImapForm((p) => ({ ...p, ssl_verify: v }))}
                >
                  Verify TLS certificate
                </Switch>
              </div>
              <p className="text-xs text-default-500">
                Disable only if TLS inspection breaks IMAP on this machine.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button color="primary" isLoading={saving} onPress={handleSaveImap}>
                  Save IMAP
                </Button>
                <Button variant="bordered" isLoading={testImapLoading} onPress={handleTestImap}>
                  Test IMAP
                </Button>
              </div>
            </CardBody>
          </Card>
        </Tab>

        <Tab key="health" title="Health">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-4 p-6">
              <p className="text-sm text-default-500">
                Connectivity checks for database, Redis, Celery, AI service, SMTP, and IMAP.
              </p>
              <Button color="primary" variant="flat" isLoading={healthLoading} onPress={loadHealth}>
                Run health checks
              </Button>
              {healthModules.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {healthModules.map((m) => (
                    <div
                      key={m.module}
                      className="border border-divider rounded-lg p-3 flex flex-col gap-1"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-semibold capitalize">{m.module.replace('_', ' ')}</span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${
                            HEALTH_STATUS_COLOR[m.status] === 'success'
                              ? 'bg-success-100 text-success-700'
                              : m.status === 'down'
                                ? 'bg-danger-100 text-danger-700'
                                : m.status === 'degraded'
                                  ? 'bg-warning-100 text-warning-700'
                                  : 'bg-default-100 text-default-600'
                          }`}
                        >
                          {m.status}
                        </span>
                      </div>
                      <p className="text-xs text-default-500">{m.message}</p>
                      {m.latency_ms > 0 && (
                        <p className="text-xs text-default-400">{m.latency_ms} ms</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <div className="border-t border-divider pt-4 mt-2">
                <p className="font-semibold mb-2">Email simulation</p>
                <p className="text-sm text-default-500 mb-3">
                  Trigger a one-time IMAP inbox poll (cold campaign reply detection).
                </p>
                <Button variant="bordered" isLoading={simulateLoading} onPress={handleSimulateImapPoll}>
                  Poll IMAP now
                </Button>
              </div>
            </CardBody>
          </Card>
        </Tab>

        <Tab key="ai" title="AI (Optional)">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-4 p-6">
              <p className="text-sm text-default-500">
                OpenAI key for cold email content generation (recommended model: gpt-4o-mini).
              </p>
              <Input
                label="Provider"
                value={aiForm.provider}
                onValueChange={(v) => setAiForm((p) => ({ ...p, provider: v }))}
              />
              <Input
                type="password"
                label="API key"
                placeholder="Leave blank to keep current"
                value={aiForm.api_key === '********' ? '' : aiForm.api_key}
                onValueChange={(v) => setAiForm((p) => ({ ...p, api_key: v || '********' }))}
              />
              <Input
                label="Model"
                value={aiForm.model}
                onValueChange={(v) => setAiForm((p) => ({ ...p, model: v }))}
              />
              <Button color="primary" isLoading={saving} onPress={handleSaveAi}>
                Save AI settings
              </Button>
            </CardBody>
          </Card>
        </Tab>

        <Tab key="debug" title="Debug">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-5 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold">Enable frontend HTTP debug logging</p>
                  <p className="text-xs text-default-500 mt-1">
                    Module: {MODULE_DEBUG}. When enabled, all role sessions log HTTP request and
                    response details (headers, body) to the API server{' '}
                    <code className="text-xs bg-default-100 px-1 rounded">debug.log</code> for
                    verification.
                  </p>
                </div>
                <Switch
                  isSelected={debugForm.enabled}
                  onValueChange={(v) => setDebugForm((p) => ({ ...p, enabled: v }))}
                />
              </div>
              <Button color="primary" isLoading={saving} onPress={handleSaveDebug}>
                Save debug settings
              </Button>
            </CardBody>
          </Card>
        </Tab>

        <Tab key="env" title="System Env (.env)">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-4 p-6">
              <div className="bg-warning-50 text-warning-800 p-4 rounded-lg text-sm mb-2 border border-warning-200">
                <strong>Warning:</strong> Modifying these raw <code>.env</code> files can break the platform. Changes to core variables (e.g. <code>SECRET_KEY</code>, <code>DATABASES</code>) require a manual server restart to take effect.
              </div>
              <p className="text-sm font-semibold mt-2">API Backend (.env)</p>
              <Textarea
                minRows={10}
                className="font-mono text-sm"
                value={envFiles.api}
                onValueChange={(v) => setEnvFiles((p) => ({ ...p, api: v }))}
              />
              <p className="text-sm font-semibold mt-4">AI Service (.env)</p>
              <Textarea
                minRows={6}
                className="font-mono text-sm"
                value={envFiles.ai_service}
                onValueChange={(v) => setEnvFiles((p) => ({ ...p, ai_service: v }))}
              />
              <div className="mt-4">
                <Button color="primary" isLoading={saving} onPress={handleSaveEnvFiles}>
                  Save .env Files
                </Button>
              </div>
            </CardBody>
          </Card>
        </Tab>
      </Tabs>

      {message && <p className="text-sm text-default-500">{message}</p>}
    </div>
  );
}
