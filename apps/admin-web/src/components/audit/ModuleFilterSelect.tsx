'use client';

import { Select, SelectItem } from '@nextui-org/react';

export const AUDIT_MODULE_OPTIONS = [
  'auth',
  'iam',
  'config',
  'employees',
  'payroll',
  'audit',
  'hrms',
  'recruitment',
  'wfh',
  'leave',
  'attendance',
  'engagement',
  'organization',
  'expenses',
  'helpdesk',
  'marketing',
] as const;

type Props = {
  value?: string;
  onChange: (module: string) => void;
  className?: string;
};

export function ModuleFilterSelect({ value, onChange, className }: Props) {
  return (
    <Select
      className={className || 'max-w-xs'}
      label="Module"
      placeholder="All modules"
      selectedKeys={value ? [value] : []}
      onSelectionChange={(keys) => {
        const mod = Array.from(keys)[0] as string | undefined;
        onChange(mod || '');
      }}
    >
      {AUDIT_MODULE_OPTIONS.map((mod) => (
        <SelectItem key={mod} textValue={mod}>
          {mod}
        </SelectItem>
      ))}
    </Select>
  );
}
