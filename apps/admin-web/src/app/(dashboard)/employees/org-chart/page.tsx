'use client';

import { useMemo, useState } from 'react';
import { Input, Spinner } from '@nextui-org/react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { employeesApi } from '@/lib/hrmsApi';
import { OrgChartTree, type OrgTreeNode } from '@/components/org/OrgChartTree';

export default function OrgChartPage() {
  const [search, setSearch] = useState('');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['employees-org-tree'],
    queryFn: async () => {
      const res = await employeesApi.orgTree();
      return res.data as { roots: OrgTreeNode[]; meta: { total: number } };
    },
  });

  const roots = useMemo(() => data?.roots ?? [], [data?.roots]);
  const total = data?.meta?.total ?? 0;

  return (
    <div className="flex w-full flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground">Organization Chart</h1>
          <p className="mt-1 text-sm text-default-500">
            Reporting hierarchy for your organization ({total} active employees).
          </p>
        </div>
        <Input
          isClearable
          className="w-full sm:max-w-xs"
          placeholder="Search by name, role, or code…"
          startContent={<Search className="text-default-400" size={18} />}
          value={search}
          onClear={() => setSearch('')}
          onValueChange={setSearch}
          variant="bordered"
          radius="lg"
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="rounded-3xl border border-divider bg-content1/60 p-4 shadow-lg backdrop-blur-xl sm:p-8"
      >
        {isLoading ? (
          <div className="flex justify-center py-24">
            <Spinner label="Loading organization chart…" color="primary" size="lg" />
          </div>
        ) : isError ? (
          <p className="py-12 text-center text-danger">Unable to load organization chart.</p>
        ) : (
          <OrgChartTree roots={roots} searchQuery={search.trim()} />
        )}
      </motion.div>
    </div>
  );
}
