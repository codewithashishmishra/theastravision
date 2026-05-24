import DashboardLayout from '@/components/layouts/DashboardLayout';
import { AuthProvider } from '@/lib/AuthProvider';
import { CooldownProvider } from '@/components/platform/CooldownProvider';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <CooldownProvider>
        <DashboardLayout>{children}</DashboardLayout>
      </CooldownProvider>
    </AuthProvider>
  );
}
