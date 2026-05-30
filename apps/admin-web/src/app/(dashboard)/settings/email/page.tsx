'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardBody, Button, Input, Spinner } from '@nextui-org/react';
import { tenantEmailApi } from '@/lib/hrmsApi';
import { useAuth } from '@/lib/AuthProvider';

type TenantEmailSettings = {
  from_email: string;
  from_name: string;
  reply_to: string;
  notify_roles: string[];
  using_platform_fallback?: boolean;
};

export default function TenantEmailSettingsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState<TenantEmailSettings>({
    from_email: '',
    from_name: 'AastraaHR',
    reply_to: '',
    notify_roles: ['Company Admin', 'HR Admin'],
  });

  useEffect(() => {
    tenantEmailApi
      .get()
      .then((res) => {
        setForm({
          from_email: res.data.from_email || '',
          from_name: res.data.from_name || 'AastraaHR',
          reply_to: res.data.reply_to || '',
          notify_roles: res.data.notify_roles || ['Company Admin', 'HR Admin'],
          using_platform_fallback: res.data.using_platform_fallback,
        });
      })
      .catch(() => setMessage('Failed to load email settings.'))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!form.from_email) {
      setMessage('From email is required.');
      return;
    }
    setSaving(true);
    setMessage('');
    try {
      await tenantEmailApi.update({
        from_email: form.from_email,
        from_name: form.from_name,
        reply_to: form.reply_to,
        notify_roles: form.notify_roles,
      });
      setMessage('Email settings saved.');
    } catch {
      setMessage('Failed to save email settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage('');
    try {
      const res = await tenantEmailApi.testSend(user?.email);
      setMessage(
        res.data.ok
          ? `Test email sent to ${user?.email || 'your address'}.`
          : `Test failed: ${res.data.smtp_error || 'unknown error'}`,
      );
    } catch {
      setMessage('Test send failed.');
    } finally {
      setTesting(false);
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
    <div className="w-full max-w-2xl flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-extrabold text-foreground">Email Settings</h1>
        <p className="text-default-500 mt-1">
          Configure the sender identity for recruitment, interviews, and other tenant emails.
          Delivery uses the platform SMTP server.
        </p>
        {form.using_platform_fallback && (
          <p className="text-warning text-sm mt-2">
            Using platform default From address until you save tenant settings.
          </p>
        )}
      </div>

      <Card className="border border-divider shadow-sm">
        <CardBody className="gap-4 p-6">
          <Input
            label="From email"
            isRequired
            value={form.from_email}
            onValueChange={(v) => setForm((p) => ({ ...p, from_email: v }))}
          />
          <Input
            label="From name"
            value={form.from_name}
            onValueChange={(v) => setForm((p) => ({ ...p, from_name: v }))}
          />
          <Input
            label="Reply-to (optional)"
            value={form.reply_to}
            onValueChange={(v) => setForm((p) => ({ ...p, reply_to: v }))}
          />
          <div className="flex flex-wrap gap-3">
            <Button color="primary" isLoading={saving} onPress={handleSave}>
              Save
            </Button>
            <Button variant="bordered" isLoading={testing} onPress={handleTest}>
              Send test email to me
            </Button>
          </div>
        </CardBody>
      </Card>

      {message && <p className="text-sm text-default-500">{message}</p>}
    </div>
  );
}
