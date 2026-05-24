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
} from '@nextui-org/react';
import api from '@/lib/axios';

const MODULE_UTIL = 'PLATFORM_UTILIZATION';
const MODULE_SMTP = 'SMTP';
const MODULE_AI = 'AI';
const MODULE_IMAP = 'IMAP';

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
  user: string;
  password: string;
  folder: string;
  poll_interval_minutes: number;
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
  host: 'smtpout.secureserver.net',
  port: 587,
  use_tls: true,
  use_ssl: false,
  user: 'sales@theastravision.com',
  password: '',
  from_email: 'sales@theastravision.com',
  from_name: 'The Astra Vision',
  rate_per_minute: 30,
};

const AI_DEFAULTS: AiConfig = {
  provider: 'openai',
  api_key: '',
  model: 'gpt-4o-mini',
};

const IMAP_DEFAULTS: ImapConfig = {
  host: 'imap.secureserver.net',
  port: 993,
  use_ssl: true,
  user: 'sales@theastravision.com',
  password: '',
  folder: 'INBOX',
  poll_interval_minutes: 5,
};

async function loadModule<T>(module: string, defaults: T): Promise<{ id: string | null; form: T }> {
  try {
    const res = await api.get<EnvConfigRow<T>>(`/env-configs/${module}/`);
    const merged = { ...defaults, ...res.data.decrypted_config };
    if (module === MODULE_SMTP && merged.password) {
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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const [utilId, setUtilId] = useState<string | null>(null);
  const [utilForm, setUtilForm] = useState<UtilizationConfig>(UTIL_DEFAULTS);

  const [smtpId, setSmtpId] = useState<string | null>(null);
  const [smtpForm, setSmtpForm] = useState<SmtpConfig>(SMTP_DEFAULTS);

  const [aiId, setAiId] = useState<string | null>(null);
  const [aiForm, setAiForm] = useState<AiConfig>(AI_DEFAULTS);

  const [imapId, setImapId] = useState<string | null>(null);
  const [imapForm, setImapForm] = useState<ImapConfig>(IMAP_DEFAULTS);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [util, smtp, ai, imap] = await Promise.all([
        loadModule(MODULE_UTIL, UTIL_DEFAULTS),
        loadModule(MODULE_SMTP, SMTP_DEFAULTS),
        loadModule(MODULE_AI, AI_DEFAULTS),
        loadModule(MODULE_IMAP, IMAP_DEFAULTS),
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
                GoDaddy: host <strong>smtpout.secureserver.net</strong>, port 587 with TLS. If auth
                fails, try port 465 with SSL enabled.
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
              </div>
              <Button color="primary" isLoading={saving} onPress={handleSaveSmtp}>
                Save SMTP
              </Button>
            </CardBody>
          </Card>
        </Tab>

        <Tab key="imap" title="IMAP (Replies)">
          <Card className="border border-divider shadow-sm mt-4">
            <CardBody className="gap-4 p-6">
              <p className="text-sm text-default-500">
                Inbound mailbox for cold campaign reply detection. Celery polls every 5 minutes.
                GoDaddy: <strong>imap.secureserver.net</strong> port 993 SSL.
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
              <Switch
                isSelected={imapForm.use_ssl}
                onValueChange={(v) => setImapForm((p) => ({ ...p, use_ssl: v }))}
              >
                Use SSL
              </Switch>
              <Button color="primary" isLoading={saving} onPress={handleSaveImap}>
                Save IMAP
              </Button>
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
      </Tabs>

      {message && <p className="text-sm text-default-500">{message}</p>}
    </div>
  );
}
