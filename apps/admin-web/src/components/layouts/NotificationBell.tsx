'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Button, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Chip } from '@nextui-org/react';
import { Bell } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/lib/hrmsApi';
import { unwrapList } from '@/lib/hrmsApi';
import { getAccessToken } from '@/lib/tokenStore';

type Notification = {
  id: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

function wsUrl() {
  const token = typeof window !== 'undefined' ? getAccessToken() : '';
  const base = process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000';
  return `${base}/ws/notifications/?token=${token}`;
}

const REST_POLL_MS = 60_000;

export function NotificationBell() {
  const queryClient = useQueryClient();
  const [live, setLive] = useState<Notification[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const invalidateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scheduleUnreadInvalidate = useCallback(() => {
    if (invalidateTimerRef.current) clearTimeout(invalidateTimerRef.current);
    invalidateTimerRef.current = setTimeout(() => {
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
    }, 500);
  }, [queryClient]);

  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => {
      const res = await notificationsApi.list();
      return unwrapList<Notification>(res.data);
    },
    refetchInterval: wsConnected ? false : REST_POLL_MS,
  });

  const { data: unreadData } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: async () => {
      const res = await notificationsApi.unreadCount();
      return res.data.count as number;
    },
    refetchInterval: wsConnected ? false : REST_POLL_MS,
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
    },
  });

  const items = live.length ? live : (data ?? []);
  const unread = unreadData ?? items.filter((n) => !n.is_read).length;

  const onMessage = useCallback(
    (n: Notification) => {
      setLive((prev) => [n, ...prev.filter((x) => x.id !== n.id)].slice(0, 50));
      scheduleUnreadInvalidate();
    },
    [scheduleUnreadInvalidate]
  );

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    let reconnectAttempt = 0;
    let cancelled = false;

    const connectWs = () => {
      if (cancelled || (typeof document !== 'undefined' && document.hidden)) return;
      try {
        ws = new WebSocket(wsUrl());
        ws.onopen = () => {
          reconnectAttempt = 0;
          setWsConnected(true);
        };
        ws.onerror = () => {};
        ws.onmessage = (ev) => {
          const payload = JSON.parse(ev.data);
          onMessage(payload);
        };
        ws.onclose = () => {
          setWsConnected(false);
          if (cancelled) return;
          const delay = Math.min(30_000, 5_000 * 2 ** reconnectAttempt);
          reconnectAttempt += 1;
          reconnectTimer = setTimeout(connectWs, delay);
        };
      } catch {
        setWsConnected(false);
      }
    };

    connectWs();

    const onVisibility = () => {
      if (document.hidden) {
        ws?.close();
        ws = null;
        setWsConnected(false);
        if (reconnectTimer) clearTimeout(reconnectTimer);
      } else if (!cancelled) {
        reconnectAttempt = 0;
        connectWs();
      }
    };
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      cancelled = true;
      document.removeEventListener('visibilitychange', onVisibility);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (invalidateTimerRef.current) clearTimeout(invalidateTimerRef.current);
      ws?.close();
      setWsConnected(false);
    };
  }, [onMessage]);

  return (
    <Dropdown placement="bottom-end">
      <DropdownTrigger>
        <Button isIconOnly variant="light" radius="full" className="text-default-500 relative hover:text-foreground">
          <Bell size={20} />
          {unread > 0 && (
            <span className="absolute top-2 right-2 min-w-[8px] h-2 px-0.5 bg-primary rounded-full text-[10px]" />
          )}
        </Button>
      </DropdownTrigger>
      <DropdownMenu aria-label="Notifications" className="max-h-80 overflow-auto w-80">
        {items.length === 0 ? (
          <DropdownItem key="empty" isReadOnly>No notifications</DropdownItem>
        ) : (
          items.slice(0, 15).map((n) => (
            <DropdownItem
              key={n.id}
              description={n.message}
              onPress={() => !n.is_read && markRead.mutate(n.id)}
            >
              <span className="flex items-center gap-2">
                {!n.is_read && <Chip size="sm" color="primary" variant="dot">New</Chip>}
                {n.title}
              </span>
            </DropdownItem>
          ))
        )}
      </DropdownMenu>
    </Dropdown>
  );
}
