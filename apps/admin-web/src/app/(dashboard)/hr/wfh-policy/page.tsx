'use client';

import { useEffect, useState } from 'react';
import { Button, Card, CardBody, Input, Switch } from '@nextui-org/react';
import { parseApiError } from '@/lib/parseApiError';
import { wfhApi } from '@/lib/wfhApi';

export default function HRWFHPolicyPage() {
  const [policy, setPolicy] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    wfhApi
      .getPolicy()
      .then((r) => {
        setPolicy(r.data);
        setError(null);
      })
      .catch((e) => setError(parseApiError(e, 'Could not load WFH policy')));
  }, []);

  const save = async () => {
    if (!policy.id) {
      setSaveError('Policy not loaded. Fix the error above and refresh.');
      return;
    }
    setLoading(true);
    setSaveError(null);
    setSaved(false);
    try {
      const res = await wfhApi.updatePolicy(policy);
      setPolicy(res.data);
      setSaved(true);
    } catch (e) {
      setSaveError(parseApiError(e, 'Save failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="text-3xl font-extrabold">WFH Policy</h1>
      {error && (
        <p className="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</p>
      )}
      {saveError && (
        <p className="text-danger text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{saveError}</p>
      )}
      {saved && (
        <p className="text-success text-sm bg-success/10 border border-success/30 rounded-lg px-4 py-3">
          Policy saved successfully.
        </p>
      )}
      <Card>
        <CardBody className="gap-4 max-w-xl">
          <Switch
            isSelected={!!policy.require_hr_approval}
            onValueChange={(v) => setPolicy((p) => ({ ...p, require_hr_approval: v }))}
            isDisabled={!policy.id}
          >
            Require HR approval after manager
          </Switch>
          <Input
            type="number"
            label="Screenshot interval (seconds)"
            value={String(policy.screenshot_interval_seconds ?? 15)}
            onValueChange={(v) => setPolicy((p) => ({ ...p, screenshot_interval_seconds: Number(v) }))}
            isDisabled={!policy.id}
          />
          <Input
            type="number"
            label="Idle threshold (seconds)"
            value={String(policy.idle_threshold_seconds ?? 300)}
            onValueChange={(v) => setPolicy((p) => ({ ...p, idle_threshold_seconds: Number(v) }))}
            isDisabled={!policy.id}
          />
          <Input
            type="number"
            label="Screenshot retention (days)"
            value={String(policy.screenshot_retention_days ?? 30)}
            onValueChange={(v) => setPolicy((p) => ({ ...p, screenshot_retention_days: Number(v) }))}
            isDisabled={!policy.id}
          />
          <Switch
            isSelected={!!policy.allow_pause}
            onValueChange={(v) => setPolicy((p) => ({ ...p, allow_pause: v }))}
            isDisabled={!policy.id}
          >
            Allow pause during session
          </Switch>
          <Button color="primary" onPress={save} isLoading={loading} isDisabled={!policy.id}>
            Save policy
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}
