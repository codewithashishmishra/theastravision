'use client';

import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { logout } from '@/lib/logout';

export function useLogout() {
  const queryClient = useQueryClient();

  return useCallback(async () => {
    await logout({ queryClient, redirect: true });
  }, [queryClient]);
}
