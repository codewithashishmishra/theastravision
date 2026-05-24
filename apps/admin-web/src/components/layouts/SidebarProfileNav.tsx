'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { profileNavItem } from '@/config/menuConfig';
import { employeesApi } from '@/lib/hrmsApi';
import { EMPLOYEE_ME_QUERY_KEY, EmployeeMeProfile } from '@/lib/employeeMe';
import { useAuthReady } from '@/lib/AuthProvider';

const PROFILE_PREFIX = '/ess/profile';

export function SidebarProfileNav() {
  const pathname = usePathname();
  const isAuthReady = useAuthReady();
  const onProfileRoute = pathname.startsWith(PROFILE_PREFIX);

  const [expanded, setExpanded] = useState(onProfileRoute);

  useEffect(() => {
    if (onProfileRoute) setExpanded(true);
  }, [onProfileRoute]);

  const { data } = useQuery({
    queryKey: [EMPLOYEE_ME_QUERY_KEY],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await employeesApi.me.get();
      return res.data as EmployeeMeProfile;
    },
    staleTime: 60_000,
  });

  const hasEmployee = data?.has_employee ?? false;

  const visibleChildren = useMemo(() => {
    const children = profileNavItem.children ?? [];
    return children.filter((child) => {
      if (child.key === 'prof-info') return true;
      return hasEmployee;
    });
  }, [hasEmployee]);

  const isParentActive =
    onProfileRoute ||
    visibleChildren.some((c) => c.path && pathname.startsWith(c.path));
  const effectivelyActive = isParentActive;

  const Icon = profileNavItem.icon;

  return (
    <div className="flex flex-col mb-2">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="block relative w-full px-3 py-1 text-left"
        aria-expanded={expanded}
      >
        <div
          className={`flex items-center justify-between px-4 py-2.5 rounded-xl transition-all ${effectivelyActive ? 'bg-primary/10' : 'hover:bg-default-100/50'}`}
        >
          <div
            className={`flex items-center gap-3 ${effectivelyActive ? 'text-primary' : 'text-default-500 hover:text-default-700'}`}
          >
            {Icon && (
              <Icon
                size={20}
                className={effectivelyActive ? 'text-primary' : 'text-default-400'}
              />
            )}
            <span
              className={`text-[15px] tracking-wide ${effectivelyActive ? 'font-semibold' : 'font-medium'}`}
            >
              {profileNavItem.label}
            </span>
          </div>
          {effectivelyActive && (
            <div className="w-1.5 h-5 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--nextui-primary),0.6)]" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="flex flex-col mt-1 mb-2">
          {visibleChildren.map((child) => {
            const isChildActive = child.path ? pathname.startsWith(child.path) : false;
            return (
              <Link
                key={child.key}
                href={child.path || '#'}
                className="block relative w-full px-3 py-0.5"
              >
                <div
                  className={`flex items-center px-12 py-2 rounded-xl transition-all ${isChildActive ? 'text-primary bg-primary/5' : 'text-default-500 hover:text-foreground hover:bg-default-100/50'}`}
                >
                  <span className={`text-[14px] ${isChildActive ? 'font-bold' : 'font-medium'}`}>
                    {child.label}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
