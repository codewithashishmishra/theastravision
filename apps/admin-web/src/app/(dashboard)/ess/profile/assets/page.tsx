'use client';

import React from 'react';
import {
  Card,
  CardBody,
  Spinner,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
} from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { employeesApi } from '@/lib/hrmsApi';
import {
  EMPLOYEE_ME_QUERY_KEY,
  EmployeeMeAsset,
  EmployeeMeProfile,
} from '@/lib/employeeMe';
import { useAuthReady } from '@/lib/AuthProvider';
import { parseApiError } from '@/lib/parseApiError';

export default function MyAssetsPage() {
  const isAuthReady = useAuthReady();

  const profileQuery = useQuery({
    queryKey: [EMPLOYEE_ME_QUERY_KEY],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await employeesApi.me.get();
      return res.data as EmployeeMeProfile;
    },
  });

  const assetsQuery = useQuery({
    queryKey: ['employee-me-assets'],
    enabled: isAuthReady && profileQuery.data?.has_employee === true,
    queryFn: async () => {
      const res = await employeesApi.me.assets();
      return res.data as EmployeeMeAsset[];
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
      <div className="max-w-3xl mx-auto p-6 md:p-8">
        <h1 className="text-2xl font-bold mb-2">My Assets</h1>
        <Card className="border border-divider/40">
          <CardBody>
            <p className="text-default-500 text-sm">
              Asset assignments are not available for your account type. Only users with a linked
              HR employee profile can view assigned equipment here.
            </p>
          </CardBody>
        </Card>
      </div>
    );
  }

  if (assetsQuery.isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (assetsQuery.error) {
    return (
      <div className="p-8 text-danger">{parseApiError(assetsQuery.error, 'Failed to load assets')}</div>
    );
  }

  const assets = assetsQuery.data ?? [];

  return (
    <div className="max-w-4xl mx-auto p-6 md:p-8 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">My Assets</h1>
        <p className="text-default-500 text-sm mt-1">Equipment assigned to you (read-only)</p>
      </div>

      {assets.length === 0 ? (
        <Card className="border border-divider/40 bg-default-50/30">
          <CardBody>
            <p className="text-default-500 text-sm">No assets are currently assigned to you.</p>
          </CardBody>
        </Card>
      ) : (
        <Table aria-label="My assigned assets" classNames={{ wrapper: 'border border-divider/40' }}>
          <TableHeader>
            <TableColumn>ASSET</TableColumn>
            <TableColumn>SERIAL</TableColumn>
            <TableColumn>CATEGORY</TableColumn>
            <TableColumn>STATUS</TableColumn>
            <TableColumn>ASSIGNED</TableColumn>
          </TableHeader>
          <TableBody>
            {assets.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.asset_name}</TableCell>
                <TableCell>{row.serial_number}</TableCell>
                <TableCell>{row.category}</TableCell>
                <TableCell>{row.asset_status}</TableCell>
                <TableCell>{row.assigned_date}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
