import type { PortalConfig } from '@/lib/jobBoardApi';

export function CareerHeader({ config }: { config: PortalConfig }) {
  const brand = config.primary_color || '#2563eb';
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center gap-4">
          {config.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={config.logo_url} alt="" className="h-12 w-auto object-contain" />
          ) : (
            <div
              className="h-12 w-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
              style={{ backgroundColor: brand }}
            >
              {config.tenant_name.charAt(0)}
            </div>
          )}
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{config.tenant_name}</h1>
            <p className="text-sm text-gray-500">Careers</p>
          </div>
        </div>
        {config.company_blurb && (
          <p className="mt-4 text-gray-600 max-w-2xl">{config.company_blurb}</p>
        )}
      </div>
    </header>
  );
}
