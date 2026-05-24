'use client';

import React, { useState } from 'react';
import { Card, CardBody, Button, Input, Switch, Spinner } from '@nextui-org/react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationApi, attendanceApi } from '@/lib/hrmsApi';
import { unwrapList } from '@/lib/hrmsApi';

export default function OrganizationProfilePage() {
  const qc = useQueryClient();
  const { data: profiles, isLoading } = useQuery({
    queryKey: ['company-profiles'],
    queryFn: async () => {
      const res = await organizationApi.companyProfiles.list();
      return unwrapList(res.data);
    },
  });
  const { data: attSettings } = useQuery({
    queryKey: ['attendance-settings'],
    queryFn: async () => (await attendanceApi.settings.get()).data,
  });

  const [form, setForm] = useState<Record<string, string>>({});

  const saveProfile = useMutation({
    mutationFn: async () => {
      const p = profiles?.[0] as { id?: string } | undefined;
      if (p?.id) return organizationApi.companyProfiles.update(p.id, form);
      return organizationApi.companyProfiles.create(form);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['company-profiles'] }),
  });

  const saveAtt = useMutation({
    mutationFn: (data: Record<string, unknown>) => attendanceApi.settings.update(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['attendance-settings'] }),
  });

  const profile = profiles?.[0] as Record<string, string> | undefined;

  return (
    <div className="w-full flex flex-col gap-6 max-w-3xl">
      <h1 className="text-3xl font-extrabold">Company Profile & Punch Settings</h1>
      {isLoading ? <Spinner /> : (
        <>
          <Card className="border border-divider">
            <CardBody className="gap-4">
              <Input label="Legal Name" defaultValue={profile?.legal_name} onValueChange={(v) => setForm((f) => ({ ...f, legal_name: v }))} />
              <Input label="Website" defaultValue={profile?.website} onValueChange={(v) => setForm((f) => ({ ...f, website: v }))} />
              <Button color="primary" isLoading={saveProfile.isPending} onPress={() => saveProfile.mutate()}>Save Profile</Button>
            </CardBody>
          </Card>
          <Card className="border border-divider">
            <CardBody className="gap-4">
              <h2 className="font-bold text-lg">Attendance / Geofence</h2>
              <Input
                label="Default radius (meters)"
                type="number"
                defaultValue={String(attSettings?.default_radius_meters ?? 50)}
                onValueChange={(v) => saveAtt.mutate({ default_radius_meters: Number(v) })}
              />
              <Switch
                isSelected={attSettings?.require_gps ?? true}
                onValueChange={(v) => saveAtt.mutate({ require_gps: v })}
              >
                Require GPS
              </Switch>
              <Switch
                isSelected={attSettings?.require_selfie ?? false}
                onValueChange={(v) => saveAtt.mutate({ require_selfie: v })}
              >
                Require selfie punch-in
              </Switch>
              <Switch
                isSelected={attSettings?.allow_web_punch ?? true}
                onValueChange={(v) => saveAtt.mutate({ allow_web_punch: v })}
              >
                Allow web punch
              </Switch>
              <Input
                label="Office start time"
                type="time"
                defaultValue={String(attSettings?.work_start_time ?? '09:00').slice(0, 5)}
                onValueChange={(v) => saveAtt.mutate({ work_start_time: v })}
              />
              <Input
                label="Office end time"
                type="time"
                defaultValue={String(attSettings?.work_end_time ?? '18:00').slice(0, 5)}
                onValueChange={(v) => saveAtt.mutate({ work_end_time: v })}
              />
              <Input
                label="Office timezone"
                defaultValue={String(attSettings?.office_hours_timezone ?? 'UTC')}
                onValueChange={(v) => saveAtt.mutate({ office_hours_timezone: v })}
              />
              <Input
                label="Work days (ISO weekdays comma-separated, e.g. 1,2,3,4,5)"
                defaultValue={(attSettings?.work_days ?? [1, 2, 3, 4, 5]).join(',')}
                onValueChange={(v) =>
                  saveAtt.mutate({
                    work_days: v
                      .split(',')
                      .map((n) => Number(n.trim()))
                      .filter((n) => Number.isInteger(n) && n >= 1 && n <= 7),
                  })
                }
              />
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
