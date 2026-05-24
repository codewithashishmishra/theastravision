'use client';

import React from 'react';
import { Card, CardBody, CardHeader, Spinner } from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { employeesApi } from '@/lib/hrmsApi';
import {
  EMPLOYEE_ME_QUERY_KEY,
  EmployeeMeBank,
  EmployeeMeProfile,
} from '@/lib/employeeMe';
import { useAuthReady } from '@/lib/AuthProvider';
import { parseApiError } from '@/lib/parseApiError';

function ReadOnlyField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-semibold text-default-500 uppercase tracking-wide">{label}</span>
      <span className="text-sm text-foreground">{value || '—'}</span>
    </div>
  );
}

export default function BankDetailsPage() {
  const isAuthReady = useAuthReady();

  const profileQuery = useQuery({
    queryKey: [EMPLOYEE_ME_QUERY_KEY],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await employeesApi.me.get();
      return res.data as EmployeeMeProfile;
    },
  });

  const bankQuery = useQuery({
    queryKey: ['employee-me-bank'],
    enabled: isAuthReady && profileQuery.data?.has_employee === true,
    queryFn: async () => {
      try {
        const res = await employeesApi.me.bank();
        return res.data as EmployeeMeBank;
      } catch (err) {
        if (err instanceof AxiosError && err.response?.status === 404) {
          return null;
        }
        throw err;
      }
    },
  });

  if (profileQuery.isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (profileQuery.error) {
    return (
      <div className="p-8 text-danger">
        {parseApiError(profileQuery.error, 'Failed to load profile')}
      </div>
    );
  }

  if (!profileQuery.data?.has_employee) {
    return (
      <div className="max-w-2xl mx-auto p-6 md:p-8">
        <h1 className="text-2xl font-bold mb-2">Bank Details</h1>
        <Card className="border border-divider/40">
          <CardBody>
            <p className="text-default-500 text-sm">
              Bank details are not available for your account type. Only users with a linked HR
              employee profile can view bank information here.
            </p>
          </CardBody>
        </Card>
      </div>
    );
  }

  if (bankQuery.isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (bankQuery.error) {
    return (
      <div className="p-8 text-danger">{parseApiError(bankQuery.error, 'Failed to load bank details')}</div>
    );
  }

  const bank = bankQuery.data;

  return (
    <div className="max-w-2xl mx-auto p-6 md:p-8 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Bank Details</h1>
        <p className="text-default-500 text-sm mt-1">Salary account on file (read-only)</p>
      </div>

      {bank ? (
        <Card className="border border-divider/40">
          <CardHeader className="pb-0">
            <h2 className="text-lg font-semibold">Account</h2>
          </CardHeader>
          <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ReadOnlyField label="Bank name" value={bank.bank_name} />
            <ReadOnlyField label="Account type" value={bank.account_type} />
            <ReadOnlyField label="Account number" value={bank.account_number_masked} />
            <ReadOnlyField label="IFSC code" value={bank.ifsc_code} />
          </CardBody>
        </Card>
      ) : (
        <Card className="border border-divider/40 bg-default-50/30">
          <CardBody>
            <p className="text-default-500 text-sm">
              No bank details are on file yet. Contact HR or payroll if you need to register your
              account.
            </p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
