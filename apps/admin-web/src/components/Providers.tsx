'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NextUIProvider } from '@nextui-org/react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { E2EEProvider } from '@/lib/e2ee/E2EEProvider';

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );
  const router = useRouter();

  return (
    <QueryClientProvider client={queryClient}>
      <NextUIProvider navigate={router.push}>
        <NextThemesProvider attribute="class" defaultTheme="dark" themes={['light', 'dark', 'tenant-dark', 'tenant-light']}>
          <E2EEProvider>{children}</E2EEProvider>
        </NextThemesProvider>
      </NextUIProvider>
    </QueryClientProvider>
  );
}
