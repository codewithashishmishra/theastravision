'use client';

import { useEffect, useState } from 'react';
import { Select, SelectItem } from '@nextui-org/react';
import api from '@/lib/axios';

type Tenant = { id: string; name: string };

type Props = {
  value?: string;
  onChange: (tenantId: string) => void;
  className?: string;
};

export function TenantFilterSelect({ value, onChange, className }: Props) {
  const [tenants, setTenants] = useState<Tenant[]>([]);

  useEffect(() => {
    api.get('/tenants/').then((res) => {
      const list = Array.isArray(res.data) ? res.data : res.data?.results || [];
      setTenants(list.map((t: { id: string; name: string }) => ({ id: String(t.id), name: t.name })));
    }).catch(() => setTenants([]));
  }, []);

  return (
    <Select
      className={className || 'max-w-xs'}
      label="Tenant"
      placeholder="All tenants"
      selectedKeys={value ? [value] : []}
      onSelectionChange={(keys) => {
        const id = Array.from(keys)[0] as string | undefined;
        onChange(id || '');
      }}
    >
      {tenants.map((t) => (
        <SelectItem key={t.id} textValue={t.name}>
          {t.name}
        </SelectItem>
      ))}
    </Select>
  );
}
