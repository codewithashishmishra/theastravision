'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@nextui-org/react';
import { getRoleHomeRoute } from '@/lib/roleRouting';
import type { Role } from '@/config/menuConfig';

export default function DashboardNotFound() {
  const [homeHref, setHomeHref] = useState('/dashboards/employee');

  useEffect(() => {
    const role = (localStorage.getItem('user_role') || 'Employee') as Role;
    setHomeHref(getRoleHomeRoute(role));
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-[70vh] text-center gap-4">
      <h1 className="text-3xl font-extrabold">Page not found</h1>
      <p className="text-default-500 max-w-md">
        The page you requested does not exist or may have been moved.
      </p>
      <Button as={Link} href={homeHref} color="primary" variant="flat" className="font-bold">
        Return to Dashboard
      </Button>
    </div>
  );
}
