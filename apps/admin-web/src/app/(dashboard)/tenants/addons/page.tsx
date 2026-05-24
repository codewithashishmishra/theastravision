'use client';

import { useState } from 'react';
import {
  Button, Card, CardBody, Chip, Select, SelectItem, Spinner, Switch, Textarea,
} from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { platformAddonsApi, tenantsApi, unwrapList } from '@/lib/hrmsApi';

type Tenant = { id: string; name: string };
type Addon = {
  id: string;
  tenant: string;
  tenant_name: string;
  addon_code: string;
  enabled: boolean;
  notes: string;
};

const JOB_PORTAL = 'job_portal';

export default function TenantAddonsPage() {
  const queryClient = useQueryClient();
  const [selectedTenant, setSelectedTenant] = useState('');
  const [notes, setNotes] = useState('');

  const { data: tenants, isLoading: tenantsLoading } = useQuery({
    queryKey: ['tenants-addons-list'],
    queryFn: async () => unwrapList<Tenant>((await tenantsApi.list()).data),
  });

  const { data: addons, isLoading: addonsLoading } = useQuery({
    queryKey: ['tenant-addons'],
    queryFn: async () => unwrapList<Addon>((await platformAddonsApi.list()).data),
  });

  const upsertMutation = useMutation({
    mutationFn: (payload: { tenant: string; addon_code: string; enabled: boolean; notes?: string }) =>
      platformAddonsApi.upsert(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tenant-addons'] }),
  });

  const currentAddon = addons?.find(
    (a) => a.tenant === selectedTenant && a.addon_code === JOB_PORTAL,
  );

  const handleToggle = (enabled: boolean) => {
    if (!selectedTenant) return;
    upsertMutation.mutate({
      tenant: selectedTenant,
      addon_code: JOB_PORTAL,
      enabled,
      notes: notes || currentAddon?.notes || '',
    });
  };

  return (
    <div className="p-6 max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tenant Add-ons</h1>
        <p className="text-default-500 text-sm mt-1">
          Enable Job Portal &amp; Career Board SDK per tenant (₹2,000/mo India · $5/mo international).
        </p>
      </div>

      <Card>
        <CardBody className="gap-4">
          {tenantsLoading ? (
            <Spinner />
          ) : (
            <Select
              label="Tenant"
              placeholder="Select company"
              selectedKeys={selectedTenant ? [selectedTenant] : []}
              onSelectionChange={(keys) => setSelectedTenant(Array.from(keys)[0] as string)}
            >
              {(tenants ?? []).map((t) => (
                <SelectItem key={t.id}>{t.name}</SelectItem>
              ))}
            </Select>
          )}

          {selectedTenant && (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Job Portal &amp; Career Board SDK</p>
                  <p className="text-xs text-default-500">Hosted careers page + embeddable job board API</p>
                </div>
                <Switch
                  isSelected={currentAddon?.enabled ?? false}
                  isDisabled={upsertMutation.isPending}
                  onValueChange={handleToggle}
                />
              </div>
              <Textarea
                label="Notes"
                value={notes || currentAddon?.notes || ''}
                onValueChange={setNotes}
                placeholder="Internal notes (optional)"
              />
              {currentAddon?.enabled && (
                <Chip color="success" variant="flat">Active</Chip>
              )}
            </>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <h2 className="font-semibold mb-3">Enabled add-ons</h2>
          {addonsLoading ? (
            <Spinner size="sm" />
          ) : (
            <ul className="space-y-2 text-sm">
              {(addons ?? []).filter((a) => a.enabled).map((a) => (
                <li key={a.id} className="flex justify-between">
                  <span>{a.tenant_name}</span>
                  <Chip size="sm" variant="flat">{a.addon_code}</Chip>
                </li>
              ))}
              {(addons ?? []).filter((a) => a.enabled).length === 0 && (
                <p className="text-default-400">No add-ons enabled yet.</p>
              )}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
