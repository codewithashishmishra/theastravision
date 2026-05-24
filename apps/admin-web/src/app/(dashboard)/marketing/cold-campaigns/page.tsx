'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Button,
  Card,
  CardBody,
  Chip,
  Input,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
  Textarea,
  useDisclosure,
} from '@nextui-org/react';
import {
  coldCampaignApi,
  ColdCampaignDetail,
  ColdCampaignListItem,
} from '@/lib/coldCampaignApi';

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'danger'> = {
  draft: 'default',
  scheduled: 'primary',
  sending: 'warning',
  sent: 'success',
  failed: 'danger',
};

export default function ColdCampaignsPage() {
  const [campaigns, setCampaigns] = useState<ColdCampaignListItem[]>([]);
  const [selected, setSelected] = useState<ColdCampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [newName, setNewName] = useState('');
  const sendModal = useDisclosure();
  const previewModal = useDisclosure();
  const [previewHtml, setPreviewHtml] = useState('');

  const loadList = useCallback(async () => {
    const res = await coldCampaignApi.list();
    const data = Array.isArray(res.data) ? res.data : (res.data as { results?: ColdCampaignListItem[] }).results ?? [];
    setCampaigns(data);
  }, []);

  const loadDetail = useCallback(async (id: string) => {
    const res = await coldCampaignApi.get(id);
    setSelected(res.data);
  }, []);

  useEffect(() => {
    loadList().finally(() => setLoading(false));
  }, [loadList]);

  const refresh = async (id?: string) => {
    await loadList();
    if (id) await loadDetail(id);
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setBusy(true);
    setMessage('');
    try {
      const res = await coldCampaignApi.create({ name: newName.trim() });
      setNewName('');
      await refresh(res.data.id);
      setMessage('Campaign created with default email template.');
    } catch {
      setMessage('Failed to create campaign.');
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    if (!selected) return;
    setBusy(true);
    setMessage('');
    try {
      await coldCampaignApi.update(selected.id, {
        name: selected.name,
        subject: selected.subject,
        body_html: selected.body_html,
        body_text: selected.body_text,
        from_name: selected.from_name,
        from_email: selected.from_email,
        trial_url: selected.trial_url,
      });
      await refresh(selected.id);
      setMessage('Campaign saved.');
    } catch {
      setMessage('Failed to save campaign.');
    } finally {
      setBusy(false);
    }
  };

  const runAction = async (fn: () => Promise<unknown>, success: string) => {
    if (!selected) return;
    setBusy(true);
    setMessage('');
    try {
      await fn();
      await refresh(selected.id);
      setMessage(success);
    } catch (err: unknown) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setMessage(detail || 'Action failed. Check SMTP settings under Platform Config.');
    } finally {
      setBusy(false);
    }
  };

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selected) return;
    setBusy(true);
    try {
      const res = await coldCampaignApi.importRecipients(selected.id, file);
      await refresh(selected.id);
      setMessage(
        `Imported ${res.data.imported} recipients (${res.data.skipped_duplicates} duplicates skipped).`,
      );
    } catch {
      setMessage('CSV import failed.');
    } finally {
      setBusy(false);
      e.target.value = '';
    }
  };

  const openRate = (c: ColdCampaignListItem) =>
    c.sent_count > 0 ? `${Math.round((c.opened_count / c.sent_count) * 100)}%` : '—';

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-6xl">
      <div>
        <h1 className="text-3xl font-extrabold">Cold Email Campaigns</h1>
        <p className="text-default-500 mt-1">
          Super Admin outreach for AastraaHR. Configure SMTP in{' '}
          <Link href="/settings/global" className="text-primary underline">
            Platform Config
          </Link>
          . Open tracking uses a 1×1 pixel; many clients block images, so opens are approximate.
        </p>
      </div>

      <Card className="border border-divider">
        <CardBody className="gap-3 p-4">
          <p className="font-semibold text-sm">New campaign</p>
          <div className="flex flex-wrap gap-2">
            <Input
              className="max-w-xs"
              placeholder="Campaign name"
              value={newName}
              onValueChange={setNewName}
            />
            <Button color="primary" isLoading={busy} onPress={handleCreate}>
              Create draft
            </Button>
          </div>
        </CardBody>
      </Card>

      <Table aria-label="Campaigns">
        <TableHeader>
          <TableColumn>Name</TableColumn>
          <TableColumn>Status</TableColumn>
          <TableColumn>Recipients</TableColumn>
          <TableColumn>Sent</TableColumn>
          <TableColumn>Opened</TableColumn>
          <TableColumn>Open rate</TableColumn>
          <TableColumn>Actions</TableColumn>
        </TableHeader>
        <TableBody emptyContent="No campaigns yet.">
          {campaigns.map((c) => (
            <TableRow key={c.id}>
              <TableCell>{c.name}</TableCell>
              <TableCell>
                <Chip size="sm" color={STATUS_COLOR[c.status] || 'default'} variant="flat">
                  {c.status}
                </Chip>
              </TableCell>
              <TableCell>{c.total_recipients}</TableCell>
              <TableCell>{c.sent_count}</TableCell>
              <TableCell>{c.opened_count}</TableCell>
              <TableCell>{openRate(c)}</TableCell>
              <TableCell>
                <Button size="sm" variant="flat" onPress={() => loadDetail(c.id)}>
                  Edit
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selected && (
        <Card className="border border-divider">
          <CardBody className="gap-4 p-6">
            <div className="flex flex-wrap justify-between items-center gap-2">
              <h2 className="text-xl font-bold">{selected.name}</h2>
              <Chip color={STATUS_COLOR[selected.status] || 'default'}>{selected.status}</Chip>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Campaign name"
                value={selected.name}
                onValueChange={(v) => setSelected({ ...selected, name: v })}
                isDisabled={selected.status !== 'draft'}
              />
              <Input
                label="Trial CTA URL"
                description="mailto or https link for 3-day trial"
                value={selected.trial_url}
                onValueChange={(v) => setSelected({ ...selected, trial_url: v })}
                isDisabled={selected.status !== 'draft'}
              />
              <Input
                label="Subject"
                className="md:col-span-2"
                value={selected.subject}
                onValueChange={(v) => setSelected({ ...selected, subject: v })}
                isDisabled={selected.status !== 'draft'}
              />
              <Textarea
                label="HTML body"
                className="md:col-span-2"
                minRows={12}
                value={selected.body_html}
                onValueChange={(v) => setSelected({ ...selected, body_html: v })}
                isDisabled={selected.status !== 'draft'}
              />
            </div>

            <p className="text-xs text-default-500">
              Merge tags: {'{{first_name}}'}, {'{{company}}'}, {'{{trial_url}}'}
            </p>

            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="flat"
                isDisabled={selected.status !== 'draft' || busy}
                onPress={() =>
                  runAction(
                    () => coldCampaignApi.loadDefaultTemplate(selected.id),
                    'Default template loaded.',
                  )
                }
              >
                Load default template
              </Button>
              <Button
                size="sm"
                variant="flat"
                isDisabled={selected.status !== 'draft' || busy}
                onPress={() =>
                  runAction(
                    () => coldCampaignApi.generateCopy(selected.id),
                    'AI rewrite applied.',
                  )
                }
              >
                AI rewrite
              </Button>
              <Button
                size="sm"
                variant="flat"
                isDisabled={busy}
                onPress={async () => {
                  const res = await coldCampaignApi.preview(selected.id, {
                    first_name: 'Alex',
                    company: 'Acme Corp',
                  });
                  setPreviewHtml(res.data.body_html);
                  previewModal.onOpen();
                }}
              >
                Preview
              </Button>
              <Button
                size="sm"
                color="secondary"
                isDisabled={busy}
                onPress={() =>
                  runAction(() => coldCampaignApi.sendTest(selected.id), 'Test email sent.')
                }
              >
                Send test to me
              </Button>
              <Button
                size="sm"
                color="primary"
                isDisabled={selected.status !== 'draft' || busy}
                onPress={handleSave}
              >
                Save
              </Button>
              <label>
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  disabled={selected.status !== 'draft' || busy}
                  onChange={handleCsvUpload}
                />
                <Button
                  as="span"
                  size="sm"
                  variant="bordered"
                  isDisabled={selected.status !== 'draft' || busy}
                >
                  Upload CSV
                </Button>
              </label>
              <Button
                size="sm"
                color="success"
                isDisabled={
                  selected.status !== 'draft' ||
                  busy ||
                  selected.total_recipients === 0
                }
                onPress={sendModal.onOpen}
              >
                Send campaign
              </Button>
              <Button
                size="sm"
                variant="light"
                isDisabled={busy}
                onPress={() => refresh(selected.id)}
              >
                Refresh stats
              </Button>
            </div>

            <p className="text-xs text-default-400">
              CSV columns: email (required), first_name, company
            </p>

            <Table aria-label="Recipients" className="mt-4">
              <TableHeader>
                <TableColumn>Email</TableColumn>
                <TableColumn>Name</TableColumn>
                <TableColumn>Company</TableColumn>
                <TableColumn>Status</TableColumn>
                <TableColumn>Opened</TableColumn>
              </TableHeader>
              <TableBody emptyContent="Upload a CSV to add recipients.">
                {(selected.recipients || []).map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.email}</TableCell>
                    <TableCell>{r.first_name || '—'}</TableCell>
                    <TableCell>{r.company || '—'}</TableCell>
                    <TableCell>{r.status}</TableCell>
                    <TableCell>
                      {r.opened_at
                        ? `Yes (${new Date(r.opened_at).toLocaleString()})`
                        : r.status === 'sent'
                          ? 'No'
                          : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardBody>
        </Card>
      )}

      {message && <p className="text-sm text-default-500">{message}</p>}

      <Modal isOpen={sendModal.isOpen} onOpenChange={sendModal.onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Send campaign</ModalHeader>
              <ModalBody>
                <p>
                  Send to <strong>{selected?.total_recipients}</strong> recipients? Only contact
                  people with a legitimate business interest. Emails include an opt-out line.
                </p>
                <p className="text-sm text-warning mt-2">
                  Requires Celery worker running. Start with small lists to warm up your mailbox.
                </p>
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>
                  Cancel
                </Button>
                <Button
                  color="success"
                  isLoading={busy}
                  onPress={async () => {
                    if (!selected) return;
                    await runAction(
                      () => coldCampaignApi.send(selected.id),
                      'Campaign send started. Refresh to see progress.',
                    );
                    onClose();
                  }}
                >
                  Confirm send
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      <Modal isOpen={previewModal.isOpen} onOpenChange={previewModal.onOpenChange} size="3xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Email preview</ModalHeader>
              <ModalBody>
                <div
                  className="border rounded-lg p-4 bg-white text-black"
                  dangerouslySetInnerHTML={{ __html: previewHtml }}
                />
              </ModalBody>
              <ModalFooter>
                <Button onPress={onClose}>Close</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
