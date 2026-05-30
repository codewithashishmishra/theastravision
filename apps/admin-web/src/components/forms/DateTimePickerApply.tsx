'use client';

import React, { useState } from 'react';
import { Button, Input, Popover, PopoverTrigger, PopoverContent, Select, SelectItem } from '@nextui-org/react';
import { Calendar } from 'lucide-react';

const HOURS = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
const MINUTES = ['00', '15', '30', '45'];

function toLocalInputValue(d: Date): { date: string; hour: string; minute: string } {
  const date = d.toISOString().slice(0, 10);
  const hour = String(d.getHours()).padStart(2, '0');
  const minute = String(d.getMinutes()).padStart(2, '0');
  const snapped = MINUTES.reduce((best, m) => {
    const diff = Math.abs(parseInt(m, 10) - d.getMinutes());
    const bestDiff = Math.abs(parseInt(best, 10) - d.getMinutes());
    return diff < bestDiff ? m : best;
  }, '00');
  return { date, hour, minute: snapped };
}

function fromParts(date: string, hour: string, minute: string): Date | null {
  if (!date) return null;
  const d = new Date(`${date}T${hour}:${minute}:00`);
  return Number.isNaN(d.getTime()) ? null : d;
}

type Props = {
  label?: string;
  value: Date | null;
  onChange: (value: Date | null) => void;
  isRequired?: boolean;
  errorMessage?: string;
};

export function DateTimePickerApply({ label = 'Scheduled time', value, onChange, isRequired, errorMessage }: Props) {
  const [open, setOpen] = useState(false);
  const initial = value ? toLocalInputValue(value) : toLocalInputValue(new Date());
  const [draftDate, setDraftDate] = useState(initial.date);
  const [draftHour, setDraftHour] = useState(initial.hour);
  const [draftMinute, setDraftMinute] = useState(initial.minute);

  const display = value
    ? value.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    : '';

  const syncDraftFromValue = () => {
    const parts = value ? toLocalInputValue(value) : toLocalInputValue(new Date());
    setDraftDate(parts.date);
    setDraftHour(parts.hour);
    setDraftMinute(parts.minute);
  };

  return (
    <Popover
      isOpen={open}
      onOpenChange={(next) => {
        if (next) syncDraftFromValue();
        setOpen(next);
      }}
      placement="bottom-start"
    >
      <PopoverTrigger>
        <Input
          label={label}
          variant="bordered"
          isRequired={isRequired}
          isReadOnly
          value={display}
          placeholder="Select date and time"
          errorMessage={errorMessage}
          isInvalid={!!errorMessage}
          startContent={<Calendar size={16} className="text-default-400" />}
          classNames={{ input: 'cursor-pointer' }}
        />
      </PopoverTrigger>
      <PopoverContent className="p-4 w-72">
        <div className="flex flex-col gap-3 w-full">
          <Input
            type="date"
            label="Date"
            size="sm"
            value={draftDate}
            onValueChange={setDraftDate}
          />
          <div className="flex gap-2">
            <Select
              label="Hour"
              size="sm"
              className="flex-1"
              selectedKeys={[draftHour]}
              onSelectionChange={(keys) => setDraftHour(String(Array.from(keys)[0] ?? '09'))}
            >
              {HOURS.map((h) => (
                <SelectItem key={h}>{h}</SelectItem>
              ))}
            </Select>
            <Select
              label="Min"
              size="sm"
              className="flex-1"
              selectedKeys={[draftMinute]}
              onSelectionChange={(keys) => setDraftMinute(String(Array.from(keys)[0] ?? '00'))}
            >
              {MINUTES.map((m) => (
                <SelectItem key={m}>{m}</SelectItem>
              ))}
            </Select>
          </div>
          <div className="flex gap-2 justify-end pt-1">
            <Button
              size="sm"
              variant="light"
              onPress={() => {
                onChange(null);
                setOpen(false);
              }}
            >
              Clear
            </Button>
            <Button
              size="sm"
              variant="flat"
              onPress={() => {
                const now = new Date();
                const parts = toLocalInputValue(now);
                setDraftDate(parts.date);
                setDraftHour(parts.hour);
                setDraftMinute(parts.minute);
              }}
            >
              Today
            </Button>
            <Button
              size="sm"
              color="primary"
              onPress={() => {
                const d = fromParts(draftDate, draftHour, draftMinute);
                if (d) onChange(d);
                setOpen(false);
              }}
            >
              Apply
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
