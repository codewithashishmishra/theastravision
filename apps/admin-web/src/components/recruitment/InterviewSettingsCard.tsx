'use client';

import { useState } from 'react';
import { Card, CardBody, Button, Input, Switch, Spinner } from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { recruitmentApi } from '@/lib/hrmsApi';

type RecruitmentSettings = {
  interview_recording_retention_days: number;
  live_watch_enabled: boolean;
};

export function InterviewSettingsCard() {
  const queryClient = useQueryClient();
  const [retentionDays, setRetentionDays] = useState('15');
  const [liveWatch, setLiveWatch] = useState(true);

  const { isLoading } = useQuery({
    queryKey: ['recruitment-settings'],
    queryFn: async () => {
      const res = await recruitmentApi.settings.get();
      const s = res.data as RecruitmentSettings;
      setRetentionDays(String(s.interview_recording_retention_days ?? 15));
      setLiveWatch(s.live_watch_enabled ?? true);
      return s;
    },
  });

  const saveMutation = useMutation({
    mutationFn: () =>
      recruitmentApi.settings.update({
        interview_recording_retention_days: Math.max(1, parseInt(retentionDays, 10) || 15),
        live_watch_enabled: liveWatch,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recruitment-settings'] }),
  });

  return (
    <Card className="border border-divider">
      <CardBody className="gap-4">
        <h2 className="font-semibold">AI interview recordings</h2>
        <p className="text-xs text-default-500">
          Recordings are stored in the database until S3 is enabled. Older media is purged automatically.
        </p>
        {isLoading ? (
          <Spinner size="sm" />
        ) : (
          <>
            <Input
              type="number"
              label="Recording retention (days)"
              description="Default 15 days. Applies to all interview video, audio, and chunks."
              value={retentionDays}
              onValueChange={setRetentionDays}
              min={1}
              max={365}
            />
            <Switch isSelected={liveWatch} onValueChange={setLiveWatch}>
              Enable HR live watch
            </Switch>
            <Button
              color="primary"
              size="sm"
              isLoading={saveMutation.isPending}
              onPress={() => saveMutation.mutate()}
            >
              Save interview settings
            </Button>
          </>
        )}
      </CardBody>
    </Card>
  );
}
