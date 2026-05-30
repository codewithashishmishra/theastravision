'use client';

import React from 'react';
import { Card, CardBody, Input, Button, Spinner } from '@nextui-org/react';
import { useAuth } from '@/lib/AuthProvider';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/axios';

export default function AccountSettingsPage() {
  const { user, refreshAuth } = useAuth();
  const [displayName, setDisplayName] = React.useState(user?.display_name ?? '');

  React.useEffect(() => {
    setDisplayName(user?.display_name ?? '');
  }, [user?.display_name]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      await api.patch('/auth/me/', { display_name: displayName });
    },
    onSuccess: () => refreshAuth(),
  });

  if (!user) {
    return (
      <div className="flex justify-center p-12">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Account Settings</h1>
        <p className="text-default-500 text-sm mt-1">Manage your profile and preferences.</p>
      </div>
      <Card>
        <CardBody className="gap-4">
          <Input label="Email" value={user.email} isReadOnly variant="bordered" />
          <Input
            label="Display Name"
            value={displayName}
            onValueChange={setDisplayName}
            variant="bordered"
          />
          {user.tenant && (
            <Input label="Organization" value={user.tenant.name} isReadOnly variant="bordered" />
          )}
          <Button
            color="primary"
            className="self-start"
            isLoading={saveMutation.isPending}
            onPress={() => saveMutation.mutate()}
          >
            Save Changes
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}
