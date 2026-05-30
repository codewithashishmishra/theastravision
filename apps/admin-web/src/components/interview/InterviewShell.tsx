'use client';

import type { ReactNode } from 'react';

const STEPS = ['Resume', 'Meet Astra', 'Pre-flight', 'Interview', 'Complete'] as const;

type Props = {
  children: ReactNode;
  step?: number;
  subtitle?: string;
  wide?: boolean;
};

export function InterviewShell({ children, step = 0, subtitle, wide = false }: Props) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-violet-900/30 via-slate-950 to-slate-950" />
      <div className="pointer-events-none absolute -right-32 top-20 h-96 w-96 rounded-full bg-orange-500/10 blur-3xl" />
      <div
        className={`relative z-10 mx-auto flex min-h-screen flex-col px-4 py-8 ${
          wide ? 'max-w-7xl' : 'max-w-3xl'
        }`}
      >
        <header className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">AastraaHR</p>
          {subtitle && <p className="mt-2 text-sm text-slate-400">{subtitle}</p>}
          <div className="mt-6 flex justify-center gap-2">
            {STEPS.map((label, i) => (
              <div
                key={label}
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  i === step
                    ? 'bg-orange-500 text-white'
                    : i < step
                      ? 'bg-slate-700 text-slate-300'
                      : 'bg-slate-800/80 text-slate-500'
                }`}
              >
                {label}
              </div>
            ))}
          </div>
        </header>
        <main className="flex flex-1 flex-col justify-center">{children}</main>
      </div>
    </div>
  );
}

export function AstraAvatar({ speaking }: { speaking?: boolean }) {
  return (
    <div
      className={`mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-orange-500 text-2xl font-bold shadow-lg shadow-orange-500/20 ${
        speaking ? 'animate-pulse ring-4 ring-orange-400/40' : ''
      }`}
    >
      A
    </div>
  );
}
