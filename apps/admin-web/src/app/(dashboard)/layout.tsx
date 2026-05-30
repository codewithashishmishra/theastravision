import { Inter } from 'next/font/google';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import { AuthProvider } from '@/lib/AuthProvider';
import { CooldownProvider } from '@/components/platform/CooldownProvider';

const inter = Inter({ subsets: ['latin'], preload: true });

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={inter.className}>
      <AuthProvider>
        <CooldownProvider>
          <DashboardLayout>{children}</DashboardLayout>
        </CooldownProvider>
      </AuthProvider>
    </div>
  );
}
