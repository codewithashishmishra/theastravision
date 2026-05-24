'use client';

import React, { useEffect, useState } from 'react';
import { Button, Card, CardBody, Switch, Checkbox } from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { useAuthReady } from '@/lib/AuthProvider';
import { getStoredJurisdictions, setStoredJurisdictions } from '@/lib/jurisdiction';

type Settings = {
  enabled_jurisdictions: string[];
  variable_pay_enabled: boolean;
  allow_employee_variable_override: boolean;
  default_currency: string;
  fiscal_year_start_month: number;
};

export default function PayrollSettingsPage() {
  const isAuthReady = useAuthReady();
  const queryClient = useQueryClient();
  const [variablePay, setVariablePay] = useState(false);
  const [allowOverride, setAllowOverride] = useState(true);
  const [jurisdictions, setJurisdictions] = useState<string[]>(['IN']);

  const { data } = useQuery({
    queryKey: ['payroll-settings'],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await api.get('/payroll/settings/');
      return res.data as Settings;
    },
  });

  useEffect(() => {
    if (data) {
      setVariablePay(data.variable_pay_enabled);
      setAllowOverride(data.allow_employee_variable_override);
      setJurisdictions(data.enabled_jurisdictions?.length ? data.enabled_jurisdictions : ['IN']);
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      await api.patch('/payroll/settings/', {
        variable_pay_enabled: variablePay,
        allow_employee_variable_override: allowOverride,
        enabled_jurisdictions: jurisdictions,
      });
      setStoredJurisdictions(jurisdictions as ('IN' | 'US' | 'CA')[]);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payroll-settings'] }),
  });

  const toggleJurisdiction = (code: string) => {
    setJurisdictions((prev) => {
      if (prev.includes(code)) {
        const next = prev.filter((j) => j !== code);
        return next.length ? next : prev;
      }
      return [...prev, code];
    });
  };

  return (
    <Card className="border border-divider max-w-2xl">
      <CardBody className="p-6 flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-extrabold">Payroll Settings</h1>
          <p className="text-sm text-default-500 mt-1">Company-wide payroll policy and variable pay.</p>
        </div>
        <div className="flex flex-col gap-3">
          <p className="font-semibold text-sm">Enabled jurisdictions</p>
          {(['IN', 'US', 'CA'] as const).map((code) => (
            <Checkbox
              key={code}
              isSelected={jurisdictions.includes(code)}
              onValueChange={() => toggleJurisdiction(code)}
            >
              {code === 'IN' ? 'India' : code === 'US' ? 'United States' : 'Canada'}
            </Checkbox>
          ))}
        </div>
        <Switch isSelected={variablePay} onValueChange={setVariablePay}>
          Enable variable pay (company-wide)
        </Switch>
        <Switch isSelected={allowOverride} onValueChange={setAllowOverride} isDisabled={!variablePay}>
          Allow per-employee variable pay override
        </Switch>
        <Button color="primary" onPress={() => saveMutation.mutate()} isLoading={saveMutation.isPending}>
          Save Settings
        </Button>
      </CardBody>
    </Card>
  );
}
