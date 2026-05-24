'use client';

import React from 'react';

export default function AppFooter({ className = '' }: { className?: string }) {
  const year = new Date().getFullYear();
  return (
    <footer
      className={`shrink-0 py-4 text-center text-xs text-default-400 border-t border-divider ${className}`}
    >
      © {year}{' '}
      <a
        href="https://theastravision.com"
        target="_blank"
        rel="noopener noreferrer"
        className="text-default-500 hover:text-primary transition-colors"
      >
        theastravision.com
      </a>
    </footer>
  );
}
