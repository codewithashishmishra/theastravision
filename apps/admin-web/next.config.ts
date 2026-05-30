import type { NextConfig } from "next";

const apiOrigin = process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1\/?$/, '') || 'http://127.0.0.1:8000';

const contentSecurityPolicy = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline'",
  `connect-src 'self' ${apiOrigin} ws://127.0.0.1:8000 ws://localhost:8000`,
  "img-src 'self' data: blob: https:",
  "media-src 'self' blob: data:",
  "font-src 'self' data:",
  "frame-ancestors 'none'",
].join('; ');

const securityHeaders = [
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(self), microphone=(self), geolocation=()' },
  { key: 'Content-Security-Policy', value: contentSecurityPolicy },
];

const nextConfig: NextConfig = {
  output: 'standalone',
  // Optional same-origin API: set NEXT_PUBLIC_API_URL=/api/v1 and use the host you browse with
  // (localhost vs 127.0.0.1) so refresh cookies are sent on hard reload.
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ];
  },
  experimental: {
    optimizePackageImports: ['@nextui-org/react', 'lucide-react', 'recharts'],
  },
  async headers() {
    return [
      { source: '/(.*)', headers: securityHeaders },
      { source: '/interview/:path*', headers: securityHeaders },
    ];
  },
};

export default nextConfig;
