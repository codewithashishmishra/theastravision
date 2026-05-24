'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Avatar, Button, Skeleton } from '@nextui-org/react';
import { useTheme } from 'next-themes';
import { Menu, Moon, Sun, X, RefreshCw, Shield } from 'lucide-react';
import { GlobalSearch } from './GlobalSearch';
import { NotificationBell } from './NotificationBell';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from '@nextui-org/react';
import { menuConfig, Role, MenuSection } from '@/config/menuConfig';
import { getStoredJurisdictions, menuVisibleForJurisdictions } from '@/lib/jurisdiction';
import { useQueryClient } from '@tanstack/react-query';
import { LogOut, Settings } from 'lucide-react';
import { clearAuthSession } from '@/lib/authSession';
import { useAuth } from '@/lib/AuthProvider';
import { getRoleHomeRoute, isDashboardPath } from '@/lib/roleRouting';
import { findMenuItemByPath, isPathAllowedForRoles } from '@/lib/menuAccess';
import { useCooldown } from '@/components/platform/CooldownProvider';
import AppFooter from '@/components/layouts/AppFooter';
import { ModuleContextFooter } from '@/components/layouts/ModuleContextFooter';
import { SidebarProfileNav } from '@/components/layouts/SidebarProfileNav';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [redirectNotice, setRedirectNotice] = useState('');

  const { isAuthReady, isAuthenticated, user, primaryRole, roles } = useAuth();
  const { isCooldown, message, pendingCount, retryAfterSeconds } = useCooldown();
  const activeRoles = useMemo(() => new Set<Role>(roles), [roles]);
  const authLoading = !isAuthReady || !isAuthenticated;
  const userEmail = user?.email ?? '';
  const userName = user?.display_name ?? '';

  useEffect(() => {
    setMounted(true);

    const storedColor = localStorage.getItem('tenant_primary_hsl');
    if (storedColor) {
      document.documentElement.style.setProperty('--nextui-primary', storedColor);
    }
  }, []);

  useEffect(() => {
    if (authLoading || activeRoles.size === 0) return;

    const allowed = isPathAllowedForRoles(pathname, activeRoles);
    if (allowed) return;

    if (isDashboardPath(pathname)) {
      const home = getRoleHomeRoute(primaryRole);
      if (pathname !== home) {
        setRedirectNotice('Redirected to your dashboard');
        router.replace(home);
      }
    }
  }, [pathname, activeRoles, authLoading, primaryRole, router]);

  const handleGlobalRefresh = async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries();
    setTimeout(() => setIsRefreshing(false), 600);
  };

  const handleLogout = () => {
    clearAuthSession();
    router.push('/login');
  };

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  const getFilteredMenu = (): MenuSection[] => {
    const tenantJurisdictions = getStoredJurisdictions();
    const filterItem = (item: { allowedRoles: Role[]; jurisdictions?: import('@/lib/jurisdiction').Jurisdiction[]; children?: typeof item[] }) => {
      if (!item.allowedRoles.some((role) => activeRoles.has(role))) return false;
      if (!menuVisibleForJurisdictions(item.jurisdictions, tenantJurisdictions)) return false;
      return true;
    };

    return menuConfig
      .map((section) => {
        const filteredItems = section.items
          .filter((item) => filterItem(item))
          .map((item) => {
            if (item.children) {
              return {
                ...item,
                children: item.children.filter((child) => filterItem(child)),
              };
            }
            return item;
          })
          .filter((item) => !item.children || item.children.length > 0);
        return { ...section, items: filteredItems };
      })
      .filter((section) => section.items.length > 0);
  };

  const filteredMenu = getFilteredMenu();
  const currentMenu = findMenuItemByPath(pathname);
  const isAuthorized =
    authLoading || !currentMenu
      ? true
      : currentMenu.allowedRoles.some((role) => activeRoles.has(role));
  const dashboardBlocked =
    !authLoading && isDashboardPath(pathname) && !isPathAllowedForRoles(pathname, activeRoles);
  const showAccessDenied = !authLoading && !isAuthorized && !isDashboardPath(pathname);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-content1 transition-transform duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 flex flex-col justify-between border-r border-divider/10`}
      >
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="flex items-center h-20 px-6 shrink-0 relative">
            <div className="flex items-center gap-3">
              <img src="/1778931708423.png" alt="AastraaHR Logo" className="w-8 h-8 rounded object-contain" />
              <span className="font-extrabold text-xl tracking-wide dark:text-white text-black">
                AASTRAA<span className="text-primary">HR</span>
              </span>
            </div>
            <Button
              isIconOnly
              variant="light"
              className="md:hidden absolute right-4 text-default-500"
              onPress={toggleSidebar}
            >
              <X size={20} />
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col py-2">
            {filteredMenu.map((section, idx) => (
              <div key={idx} className="flex flex-col mb-4">
                {section.items.map((item) => {
                  const isActive = item.path ? pathname.startsWith(item.path) : false;
                  const hasActiveChild =
                    item.children && item.children.some((c) => c.path && pathname.startsWith(c.path));
                  const effectivelyActive = isActive || hasActiveChild;

                  return (
                    <div key={item.key} className="flex flex-col">
                      <Link
                        href={item.path || (item.children ? item.children[0].path! : '#')}
                        className="block relative w-full px-3 py-1"
                      >
                        <div
                          className={`flex items-center justify-between px-4 py-2.5 rounded-xl transition-all ${effectivelyActive ? 'bg-primary/10' : 'hover:bg-default-100/50'}`}
                        >
                          <div
                            className={`flex items-center gap-3 ${effectivelyActive ? 'text-primary' : 'text-default-500 hover:text-default-700'}`}
                          >
                            {item.icon && (
                              <item.icon
                                size={20}
                                className={effectivelyActive ? 'text-primary' : 'text-default-400'}
                              />
                            )}
                            <span
                              className={`text-[15px] tracking-wide ${effectivelyActive ? 'font-semibold' : 'font-medium'}`}
                            >
                              {item.label}
                            </span>
                          </div>
                          {effectivelyActive && (
                            <div className="w-1.5 h-5 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--nextui-primary),0.6)]" />
                          )}
                        </div>
                      </Link>

                      {item.children && effectivelyActive && (
                        <div className="flex flex-col mt-1 mb-2">
                          {item.children.map((child) => {
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
                                  <span
                                    className={`text-[14px] ${isChildActive ? 'font-bold' : 'font-medium'}`}
                                  >
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
                })}
              </div>
            ))}
          </div>
        </div>

        <div className="shrink-0 px-3 pb-3 pt-2">
          {!authLoading && <SidebarProfileNav />}
          <div className="h-px w-full bg-divider/50 mx-3 my-4" />
          <div className="px-3 pb-3">
          {authLoading ? (
            <div className="flex items-center gap-4">
              <Skeleton className="rounded-full w-10 h-10" />
              <div className="flex flex-col gap-2 flex-1">
                <Skeleton className="h-4 w-24 rounded-lg" />
                <Skeleton className="h-3 w-32 rounded-lg" />
              </div>
            </div>
          ) : (
            <Dropdown placement="top-start">
              <DropdownTrigger>
                <div className="flex items-center gap-4 cursor-pointer group">
                  <Avatar
                    src={`https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=random`}
                    size="md"
                    className="ring-2 ring-transparent group-hover:ring-primary transition-all"
                  />
                  <div className="flex flex-col flex-1 overflow-hidden">
                    <span className="text-[15px] font-bold text-foreground truncate group-hover:text-primary transition-colors">
                      {userName}
                    </span>
                    <span className="text-[13px] font-medium text-default-500 truncate">{userEmail}</span>
                  </div>
                </div>
              </DropdownTrigger>
              <DropdownMenu aria-label="User Actions" variant="flat">
                <DropdownItem key="settings" startContent={<Settings size={16} />} onPress={() => router.push('/settings/global')}>
                  Account Settings
                </DropdownItem>
                <DropdownItem key="logout" color="danger" startContent={<LogOut size={16} />} onPress={handleLogout}>
                  Log Out
                </DropdownItem>
              </DropdownMenu>
            </Dropdown>
          )}
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col h-full relative w-full bg-background">
        <header className="shrink-0 h-20 bg-transparent flex items-center justify-between px-8 z-10 w-full max-w-7xl mx-auto">
          <div className="flex items-center gap-4 flex-1">
            <Button isIconOnly variant="light" className="md:hidden text-foreground" onPress={toggleSidebar}>
              <Menu size={20} />
            </Button>
            <GlobalSearch activeRoles={activeRoles} />
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <Button
              isIconOnly
              variant="light"
              radius="full"
              className="text-default-500 hover:text-foreground"
              onPress={handleGlobalRefresh}
              title="Refresh Data"
            >
              <RefreshCw size={18} className={isRefreshing ? 'animate-spin text-primary' : ''} />
            </Button>
            <NotificationBell />
            <Button
              isIconOnly
              variant="light"
              radius="full"
              className="text-default-500 hover:text-foreground"
              onPress={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
              {mounted ? (
                theme === 'dark' ? (
                  <Moon size={20} />
                ) : (
                  <Sun size={20} />
                )
              ) : (
                <div className="w-5 h-5" />
              )}
            </Button>
          </div>
        </header>

        {(isCooldown || pendingCount > 0) && (
          <div className="shrink-0 px-6 md:px-8 max-w-7xl mx-auto w-full">
            <div
              className={`mb-2 p-3 rounded-xl border text-sm font-medium ${
                isCooldown
                  ? 'bg-warning/10 border-warning/30 text-warning-700 dark:text-warning'
                  : 'bg-primary/10 border-primary/20 text-primary'
              }`}
            >
              {isCooldown ? (
                <>
                  {message}
                  {retryAfterSeconds > 0 && (
                    <span className="block mt-1 text-xs opacity-80">
                      Estimated time remaining: {Math.ceil(retryAfterSeconds / 60)} min
                    </span>
                  )}
                </>
              ) : null}
              {pendingCount > 0 && (
                <span className={isCooldown ? 'block mt-1 text-xs' : ''}>
                  {pendingCount} change{pendingCount === 1 ? '' : 's'} queued for sync.
                </span>
              )}
            </div>
          </div>
        )}

        <main className="flex-1 overflow-y-auto px-6 md:px-8 pb-4 custom-scrollbar relative z-0 min-h-0">
          <div className="max-w-7xl mx-auto w-full animate-fade-in min-h-full flex flex-col">
            {redirectNotice && (
              <div className="mb-4 p-3 rounded-xl bg-primary/10 border border-primary/20 text-sm text-primary font-medium">
                {redirectNotice}
              </div>
            )}
            {authLoading ? (
              <div className="flex flex-col gap-4 py-8">
                <Skeleton className="h-10 w-64 rounded-lg" />
                <Skeleton className="h-32 w-full rounded-xl" />
              </div>
            ) : dashboardBlocked ? (
              <div className="flex flex-col gap-4 py-8">
                <Skeleton className="h-10 w-48 rounded-lg" />
                <Skeleton className="h-32 w-full rounded-xl" />
              </div>
            ) : showAccessDenied ? (
              <div className="flex flex-col items-center justify-center h-[70vh] text-center">
                <div className="w-24 h-24 bg-danger/10 text-danger rounded-full flex items-center justify-center mb-6 shadow-inner border border-danger/20">
                  <Shield size={48} />
                </div>
                <h1 className="text-3xl font-extrabold text-foreground mb-3">Access Denied</h1>
                <p className="text-default-500 max-w-md">
                  You are not authorized to view this page. If you believe this is an error, please contact your
                  Company Admin to adjust your roles and permissions.
                </p>
                <Button
                  color="primary"
                  variant="flat"
                  className="mt-8 font-bold"
                  onPress={() => router.push(getRoleHomeRoute(primaryRole))}
                >
                  Return to Dashboard
                </Button>
              </div>
            ) : (
              children
            )}
            <ModuleContextFooter />
            <AppFooter className="mt-auto" />
          </div>
        </main>
      </div>
    </div>
  );
}
