'use client';

import { useState } from 'react';
import { Button, Input, Textarea } from '@nextui-org/react';
import { wfhApi } from '@/lib/wfhApi';

type Props = {
  onSuccess?: () => void;
};

export default function WFHRequestForm({ onSuccess }: Props) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await wfhApi.createRequest({ start_date: startDate, end_date: endDate, reason });
      onSuccess?.();
      setStartDate('');
      setEndDate('');
      setReason('');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to submit request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-4 max-w-lg">
      {error && <p className="text-danger text-sm">{error}</p>}
      <Input type="date" label="Start date" value={startDate} onValueChange={setStartDate} isRequired />
      <Input type="date" label="End date" value={endDate} onValueChange={setEndDate} isRequired />
      <Textarea label="Reason" value={reason} onValueChange={setReason} isRequired minRows={3} />
      <Button type="submit" color="primary" isLoading={loading}>
        Submit WFH Request
      </Button>
    </form>
  );
}
