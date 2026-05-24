'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/** Add Employee menu entry redirects to directory with create flow. */
export default function AddEmployeeRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/employees/directory?action=create');
  }, [router]);

  return null;
}
