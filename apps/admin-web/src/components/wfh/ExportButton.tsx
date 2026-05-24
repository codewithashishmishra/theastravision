'use client';

import { Button } from '@nextui-org/react';

type Props = {
  data: unknown[];
  filename: string;
  format?: 'csv' | 'json';
};

export default function ExportButton({ data, filename, format = 'csv' }: Props) {
  const exportData = () => {
    if (!data.length) return;
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.json`;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }
    const rows = data as Record<string, unknown>[];
    const headers = Object.keys(rows[0]);
    const csv = [
      headers.join(','),
      ...rows.map((r) => headers.map((h) => JSON.stringify(r[h] ?? '')).join(',')),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Button variant="flat" color="primary" onPress={exportData} isDisabled={!data.length}>
      Export {format.toUpperCase()}
    </Button>
  );
}
