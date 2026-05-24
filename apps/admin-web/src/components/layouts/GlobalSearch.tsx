'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import { employeesApi } from '@/lib/hrmsApi';
import { unwrapList } from '@/lib/hrmsApi';
import type { Role } from '@/config/menuConfig';

type EmployeeHit = {
  id: string;
  first_name?: string;
  last_name?: string;
  employee_code?: string;
  user?: { email?: string };
};

type GlobalSearchProps = {
  activeRoles: Set<Role>;
};

export function GlobalSearch({ activeRoles }: GlobalSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EmployeeHit[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const canSearchDirectory =
    activeRoles.has('HR Admin') ||
    activeRoles.has('Company Admin') ||
    activeRoles.has('Super Admin');

  useEffect(() => {
    if (!canSearchDirectory) {
      setResults([]);
      return;
    }
    if (!query.trim() || query.length < 2) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const res = await employeesApi.search(query.trim());
        setResults(unwrapList<EmployeeHit>(res.data));
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query, canSearchDirectory]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  if (!canSearchDirectory) {
    return null;
  }

  const select = (emp: EmployeeHit) => {
    setOpen(false);
    setQuery('');
    router.push(`/employees/directory?highlight=${emp.id}`);
  };

  return (
    <div ref={ref} className="relative hidden sm:block w-72">
      <div className="flex items-center bg-content1/50 border border-divider/50 rounded-full px-4 py-2 focus-within:border-primary/50 focus-within:bg-content1 transition-all shadow-sm">
        <Search size={18} className="text-default-400 mr-3 shrink-0" />
        <input
          type="text"
          placeholder="Search employees..."
          className="bg-transparent outline-none text-[15px] font-medium w-full text-foreground placeholder:text-default-500"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
        />
      </div>
      {open && results.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-content1 border border-divider rounded-xl shadow-lg z-50 overflow-hidden">
          {results.map((emp) => (
            <button
              key={emp.id}
              type="button"
              className="w-full text-left px-4 py-3 hover:bg-default-100 transition-colors border-b border-divider last:border-0"
              onClick={() => select(emp)}
            >
              <p className="font-semibold text-sm">
                {emp.first_name} {emp.last_name}
              </p>
              <p className="text-xs text-default-500">
                {emp.employee_code}
                {emp.user?.email ? ` · ${emp.user.email}` : ''}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
