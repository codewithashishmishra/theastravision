'use client';

import { Button, Card, CardBody, Input } from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { employeesApi } from '@/lib/hrmsApi';

export default function WorkLocationPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ['me-work-location'],
    queryFn: async () => (await employeesApi.me.workLocation()).data,
  });

  const [form, setForm] = useState({
    home_address: '',
    home_latitude: '',
    home_longitude: '',
  });

  const source = data ?? {};
  const current = {
    home_address: form.home_address || source.home_address || '',
    home_latitude: form.home_latitude || (source.home_latitude != null ? String(source.home_latitude) : ''),
    home_longitude: form.home_longitude || (source.home_longitude != null ? String(source.home_longitude) : ''),
  };

  const save = useMutation({
    mutationFn: () =>
      employeesApi.me.updateWorkLocation({
        home_address: current.home_address,
        home_latitude: current.home_latitude ? Number(current.home_latitude) : null,
        home_longitude: current.home_longitude ? Number(current.home_longitude) : null,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['me-work-location'] }),
  });

  return (
    <div className="w-full max-w-2xl">
      <Card>
        <CardBody className="gap-4">
          <h1 className="text-xl font-bold">Home Work Location</h1>
          <Input
            label="Home Address"
            value={current.home_address}
            onValueChange={(v) => setForm((f) => ({ ...f, home_address: v }))}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Home Latitude"
              type="number"
              value={current.home_latitude}
              onValueChange={(v) => setForm((f) => ({ ...f, home_latitude: v }))}
            />
            <Input
              label="Home Longitude"
              type="number"
              value={current.home_longitude}
              onValueChange={(v) => setForm((f) => ({ ...f, home_longitude: v }))}
            />
          </div>
          <p className="text-sm text-default-500">
            This is mandatory for field employees and used to prevent attendance punch from home.
          </p>
          <Button color="primary" onPress={() => save.mutate()} isLoading={save.isPending}>
            Save Location
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}
