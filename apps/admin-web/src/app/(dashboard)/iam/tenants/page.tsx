'use client';

import { useQuery } from '@tanstack/react-query';
import { Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Button, Chip } from '@nextui-org/react';
import { Plus } from 'lucide-react';
import { api } from '@/lib/api';

export default function TenantsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: async () => {
      const res = await api.get('/tenants/');
      return res.data;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold">Tenants</h2>
        <Button color="primary" endContent={<Plus size={18} />}>
          Add Tenant
        </Button>
      </div>

      <Table aria-label="Tenants Table" shadow="sm">
        <TableHeader>
          <TableColumn>NAME</TableColumn>
          <TableColumn>DOMAIN</TableColumn>
          <TableColumn>STATUS</TableColumn>
          <TableColumn>ACTIONS</TableColumn>
        </TableHeader>
        <TableBody 
          items={data || []} 
          isLoading={isLoading}
          emptyContent="No tenants to display."
        >
          {(item: any) => (
            <TableRow key={item.id}>
              <TableCell className="font-medium">{item.name}</TableCell>
              <TableCell>{item.domain || 'N/A'}</TableCell>
              <TableCell>
                <Chip size="sm" color={item.is_active ? "success" : "default"} variant="flat">
                  {item.is_active ? 'Active' : 'Inactive'}
                </Chip>
              </TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button size="sm" variant="light" color="primary">Edit</Button>
                  <Button size="sm" variant="light" color="danger">Delete</Button>
                </div>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
