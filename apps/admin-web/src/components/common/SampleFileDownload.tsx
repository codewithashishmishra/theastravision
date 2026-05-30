'use client';

import { Button } from '@nextui-org/react';
import { Download } from 'lucide-react';

type Props = {
  href: string;
  filename?: string;
  label?: string;
  size?: 'sm' | 'md';
  variant?: 'flat' | 'bordered' | 'light';
};

export function SampleFileDownload({
  href,
  filename,
  label = 'Download sample CSV',
  size = 'sm',
  variant = 'flat',
}: Props) {
  return (
    <Button
      as="a"
      href={href}
      download={filename}
      size={size}
      variant={variant}
      startContent={<Download size={16} />}
    >
      {label}
    </Button>
  );
}
