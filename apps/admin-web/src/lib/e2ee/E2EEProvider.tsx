'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { ensureE2EESession, resetE2EESession } from './handshake';
import { hasE2EESession } from './sessionStore';

type E2EEContextValue = {
  e2eeReady: boolean;
};

const E2EEContext = createContext<E2EEContextValue>({ e2eeReady: false });

export function E2EEProvider({ children }: { children: React.ReactNode }) {
  const [e2eeReady, setE2eeReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    ensureE2EESession()
      .then(() => {
        if (!cancelled) setE2eeReady(hasE2EESession());
      })
      .catch(() => {
        if (!cancelled) setE2eeReady(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return <E2EEContext.Provider value={{ e2eeReady }}>{children}</E2EEContext.Provider>;
}

export function useE2EE(): E2EEContextValue {
  return useContext(E2EEContext);
}

export { resetE2EESession };
