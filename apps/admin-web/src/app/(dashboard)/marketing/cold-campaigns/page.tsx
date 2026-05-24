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
  Select,
  SelectItem,
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
  apiErrorDetail,
  coldCampaignApi,
  ColdCampaignDetail,
  ColdCampaignListItem,
  ContentBatch,
  ContentVariant,
  LibraryVariant,
  ThreadMessage,
} from '@/lib/coldCampaignApi';
import { formatRegionalDate, formatRegionalDateTime } from '@/lib/formatDateTime';
import { sanitizeHtml } from '@/lib/sanitizeHtml';

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'danger'> = {
  draft: 'default',
  scheduled: 'primary',
  sending: 'warning',
  sent: 'success',
  failed: 'danger',
};

const REPLY_COLOR: Record<string, 'default' | 'success' | 'warning' | 'danger'> = {
  none: 'default',
  interested: 'success',
  schedule: 'success',
  replied: 'warning',
  unsubscribe: 'danger',
  other: 'default',
};

function stripHtml(html: string, max = 120): string {
  const text = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

export default function ColdCampaignsPage() {
  const [campaigns, setCampaigns] = useState<ColdCampaignListItem[]>([]);
  const [selected, setSelected] = useState<ColdCampaignDetail | null>(null);
  const [threads, setThreads] = useState<ThreadMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [newName, setNewName] = useState('');

  const wizardModal = useDisclosure();
  const sendModal = useDisclosure();
  const previewModal = useDisclosure();
  const libraryModal = useDisclosure();
  const [previewHtml, setPreviewHtml] = useState('');

  const [wizardCampaign, setWizardCampaign] = useState<ColdCampaignDetail | null>(null);
  const [followupCount, setFollowupCount] = useState('0');
  const [followupDays, setFollowupDays] = useState(['3', '7', '14']);
  const [generatedBatch, setGeneratedBatch] = useState<ContentBatch | null>(null);
  const [libraryItems, setLibraryItems] = useState<LibraryVariant[]>([]);

  const loadList = useCallback(async () => {
    const res = await coldCampaignApi.list();
    const data = Array.isArray(res.data)
      ? res.data
      : (res.data as { results?: ColdCampaignListItem[] }).results ?? [];
    setCampaigns(data);
  }, []);

  const loadThreads = useCallback(async () => {
    try {
      const res = await coldCampaignApi.listThreads();
      setThreads(Array.isArray(res.data) ? res.data : []);
    } catch {
      setThreads([]);
    }
  }, []);

  const loadDetail = useCallback(async (id: string) => {
    const res = await coldCampaignApi.get(id);
    setSelected(res.data);
  }, []);

  useEffect(() => {
    Promise.all([loadList(), loadThreads()]).finally(() => setLoading(false));
  }, [loadList, loadThreads]);

  const refresh = async (id?: string) => {
    await loadList();
    await loadThreads();
    if (id) await loadDetail(id);
  };

  const handleCreate = async () => {
    if (!newName.trim()) {
      setMessage('Enter a campaign name.');
      return;
    }
    setBusy(true);
    setMessage('');
    const count = parseInt(followupCount, 10) || 0;
    const delays = followupDays.slice(0, count).map((d) => parseInt(d, 10) || 3);
    try {
      const res = await coldCampaignApi.create({
        name: newName.trim(),
        followup_count: count,
        followup_delay_days: delays,
      });
      setNewName('');
      setWizardCampaign(res.data);
      setSelected(res.data);
      setGeneratedBatch(null);
      wizardModal.onOpen();
      await refresh(res.data.id);
      setMessage('Draft created. Generate email content in the wizard.');
    } catch (err) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const openWizardFor = async (id: string) => {
    setBusy(true);
    try {
      const res = await coldCampaignApi.get(id);
      setWizardCampaign(res.data);
      setFollowupCount(String(res.data.followup_count ?? 0));
      const days = res.data.followup_delay_days?.length
        ? res.data.followup_delay_days.map(String)
        : ['3', '7', '14'];
      setFollowupDays(days);
      setGeneratedBatch(null);
      wizardModal.onOpen();
    } catch (err) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleSaveWizardMeta = async () => {
    if (!wizardCampaign) return;
    const count = parseInt(followupCount, 10) || 0;
    const delays = followupDays.slice(0, count).map((d) => parseInt(d, 10) || 3);
    setBusy(true);
    try {
      const res = await coldCampaignApi.update(wizardCampaign.id, {
        followup_count: count,
        followup_delay_days: delays,
      });
      setWizardCampaign(res.data);
      if (selected?.id === res.data.id) setSelected(res.data);
      setMessage('Follow-up settings saved.');
    } catch (err) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleGenerate = async (objective: 'sales' | 'quick_demo') => {
    if (!wizardCampaign) return;
    setBusy(true);
    setMessage('');
    try {
      const res = await coldCampaignApi.generateVariations(wizardCampaign.id, objective);
      setGeneratedBatch(res.data);
      setMessage(`Generated 5 ${objective === 'sales' ? 'sales' : 'quick demo'} variants.`);
    } catch (err) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleApplyVariant = async (variant: ContentVariant | LibraryVariant) => {
    if (!wizardCampaign) return;
    setBusy(true);
    try {
      const res = await coldCampaignApi.applyVariant(wizardCampaign.id, variant.id);
      setWizardCampaign(res.data);
      setSelected(res.data);
      setMessage('Content applied to campaign.');
    } catch (err) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const openLibrary = async () => {
    setBusy(true);
    try {
      const res = await coldCampaignApi.contentLibrary();
      setLibraryItems(Array.isArray(res.data) ? res.data : []);
      libraryModal.onOpen();
    } catch (err) {
      setMessage(apiErrorDetail(err));
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
        followup_count: selected.followup_count,
        followup_delay_days: selected.followup_delay_days,
      });
      await refresh(selected.id);
      setMessage('Campaign saved.');
    } catch (err) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const runAction = async (fn: () => Promise<unknown>, success: string, campaignId?: string) => {
    setBusy(true);
    setMessage('');
    try {
      await fn();
      await refresh(campaignId || selected?.id);
      setMessage(success);
    } catch (err: unknown) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  };

  const handleStartCampaign = async (c: ColdCampaignListItem) => {
    setSelected(null);
    setBusy(true);
    setMessage('');
    try {
      const detail = await coldCampaignApi.get(c.id);
      if (!detail.data.subject || !detail.data.body_html) {
        setMessage('Set subject and body before sending (use wizard).');
        await openWizardFor(c.id);
        return;
      }
      if (detail.data.total_recipients === 0) {
        setMessage('Upload recipients CSV before sending.');
        setSelected(detail.data);
        return;
      }
      await coldCampaignApi.send(c.id);
      await refresh(c.id);
      setMessage('Campaign send started.');
    } catch (err) {
      setMessage(apiErrorDetail(err));
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
    } catch (err) {
      setMessage(apiErrorDetail(err));
    } finally {
      setBusy(false);
      e.target.value = '';
    }
  };

  const openRate = (c: ColdCampaignListItem) =>
    c.sent_count > 0 ? `${Math.round((c.opened_count / c.sent_count) * 100)}%` : '—';

  const renderVariantCards = (variants: ContentVariant[]) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
      {variants.map((v) => (
        <Card key={v.id} className="border border-divider">
          <CardBody className="gap-2 p-4">
            <p className="text-xs text-default-500">Variant {v.variant_index}</p>
            <p className="font-semibold text-sm">{v.subject}</p>
            <p className="text-xs text-default-400">{stripHtml(v.body_html)}</p>
            <Button
              size="sm"
              color="primary"
              isLoading={busy}
              onPress={() => handleApplyVariant(v)}
            >
              Use this
            </Button>
          </CardBody>
        </Card>
      ))}
    </div>
  );

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
          Super Admin outreach for AastraaHR. Configure SMTP and IMAP in{' '}
          <Link href="/settings/global" className="text-primary underline">
            Platform Config
          </Link>
          . AI uses your Platform Config model (e.g. gpt-4o-mini). Open tracking uses a 1×1 pixel.
        </p>
      </div>

      <Card className="border border-divider">
        <CardBody className="gap-3 p-4">
          <p className="font-semibold text-sm">New campaign</p>
          <div className="flex flex-wrap gap-2 items-end">
            <Input
              className="max-w-xs"
              placeholder="Campaign name"
              value={newName}
              onValueChange={setNewName}
            />
            <Select
              label="Follow-ups"
              className="max-w-[140px]"
              selectedKeys={[followupCount]}
              onSelectionChange={(k) => {
                const v = Array.from(k)[0] as string;
                setFollowupCount(v ?? '0');
              }}
            >
              <SelectItem key="0">None</SelectItem>
              <SelectItem key="1">1</SelectItem>
              <SelectItem key="2">2</SelectItem>
              <SelectItem key="3">3</SelectItem>
            </Select>
            {parseInt(followupCount, 10) > 0 &&
              followupDays.slice(0, parseInt(followupCount, 10)).map((d, i) => (
                <Input
                  key={i}
                  className="max-w-[100px]"
                  type="number"
                  label={`Day ${i + 1}`}
                  value={d}
                  onValueChange={(v) => {
                    const next = [...followupDays];
                    next[i] = v;
                    setFollowupDays(next);
                  }}
                />
              ))}
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
                <div className="flex gap-1 flex-wrap">
                  <Chip size="sm" color={STATUS_COLOR[c.status] || 'default'} variant="flat">
                    {c.status}
                  </Chip>
                  {c.is_paused && (
                    <Chip size="sm" color="warning" variant="flat">
                      paused
                    </Chip>
                  )}
                </div>
              </TableCell>
              <TableCell>{c.total_recipients}</TableCell>
              <TableCell>{c.sent_count}</TableCell>
              <TableCell>{c.opened_count}</TableCell>
              <TableCell>{openRate(c)}</TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  <Button size="sm" variant="flat" onPress={() => openWizardFor(c.id)}>
                    Wizard
                  </Button>
                  <Button size="sm" variant="flat" onPress={() => loadDetail(c.id)}>
                    Edit
                  </Button>
                  {c.status === 'draft' && (
                    <Button
                      size="sm"
                      color="success"
                      isDisabled={busy}
                      onPress={() => handleStartCampaign(c)}
                    >
                      Start
                    </Button>
                  )}
                  {c.status === 'sending' && !c.is_paused && (
                    <Button
                      size="sm"
                      color="warning"
                      isDisabled={busy}
                      onPress={() =>
                        runAction(() => coldCampaignApi.pause(c.id), 'Campaign paused.', c.id)
                      }
                    >
                      Pause
                    </Button>
                  )}
                  {c.status === 'sending' && c.is_paused && (
                    <Button
                      size="sm"
                      color="primary"
                      isDisabled={busy}
                      onPress={() =>
                        runAction(() => coldCampaignApi.resume(c.id), 'Campaign resumed.', c.id)
                      }
                    >
                      Resume
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {threads.length > 0 && (
        <Card className="border border-divider">
          <CardBody className="gap-3 p-4">
            <h2 className="text-lg font-bold">Notifications &amp; threads</h2>
            <p className="text-xs text-default-500">Inbound replies detected via IMAP polling.</p>
            <Table aria-label="Reply threads">
              <TableHeader>
                <TableColumn>Campaign</TableColumn>
                <TableColumn>From</TableColumn>
                <TableColumn>Classification</TableColumn>
                <TableColumn>Subject</TableColumn>
                <TableColumn>When</TableColumn>
              </TableHeader>
              <TableBody>
                {threads.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>{t.campaign_name}</TableCell>
                    <TableCell>{t.recipient_email}</TableCell>
                    <TableCell>
                      <Chip size="sm" color={REPLY_COLOR[t.classification] || 'default'} variant="flat">
                        {t.classification}
                      </Chip>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">{t.subject}</TableCell>
                    <TableCell>{formatRegionalDateTime(t.received_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardBody>
        </Card>
      )}

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
              <Button size="sm" variant="flat" isDisabled={busy} onPress={() => openWizardFor(selected.id)}>
                Open wizard
              </Button>
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
                  selected.status !== 'draft' || busy || selected.total_recipients === 0
                }
                onPress={sendModal.onOpen}
              >
                Send campaign
              </Button>
            </div>

            <Table aria-label="Recipients" className="mt-4">
              <TableHeader>
                <TableColumn>Email</TableColumn>
                <TableColumn>Status</TableColumn>
                <TableColumn>Reply</TableColumn>
                <TableColumn>Opened</TableColumn>
              </TableHeader>
              <TableBody emptyContent="Upload a CSV to add recipients.">
                {(selected.recipients || []).map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.email}</TableCell>
                    <TableCell>{r.status}</TableCell>
                    <TableCell>
                      {r.reply_status !== 'none' ? (
                        <Chip size="sm" color={REPLY_COLOR[r.reply_status] || 'default'} variant="flat">
                          {r.reply_status}
                        </Chip>
                      ) : (
                        '—'
                      )}
                    </TableCell>
                    <TableCell>
                      {r.opened_at
                        ? `Yes (${formatRegionalDateTime(r.opened_at)})`
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

      {message && (
        <p className={`text-sm ${message.toLowerCase().includes('fail') ? 'text-danger' : 'text-default-500'}`}>
          {message}
        </p>
      )}

      <Modal isOpen={wizardModal.isOpen} onOpenChange={wizardModal.onOpenChange} size="4xl" scrollBehavior="inside">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Draft wizard — {wizardCampaign?.name}</ModalHeader>
              <ModalBody className="gap-4">
                <div className="flex flex-wrap gap-2 items-end">
                  <Select
                    label="Follow-ups (max 3)"
                    className="max-w-[160px]"
                    selectedKeys={[followupCount]}
                    onSelectionChange={(k) => setFollowupCount((Array.from(k)[0] as string) ?? '0')}
                  >
                    <SelectItem key="0">None</SelectItem>
                    <SelectItem key="1">1</SelectItem>
                    <SelectItem key="2">2</SelectItem>
                    <SelectItem key="3">3</SelectItem>
                  </Select>
                  {parseInt(followupCount, 10) > 0 &&
                    followupDays.slice(0, parseInt(followupCount, 10)).map((d, i) => (
                      <Input
                        key={i}
                        className="max-w-[100px]"
                        type="number"
                        label={`Delay ${i + 1} (days)`}
                        value={d}
                        onValueChange={(v) => {
                          const next = [...followupDays];
                          next[i] = v;
                          setFollowupDays(next);
                        }}
                      />
                    ))}
                  <Button size="sm" variant="flat" isLoading={busy} onPress={handleSaveWizardMeta}>
                    Save follow-ups
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    color="primary"
                    isLoading={busy}
                    isDisabled={wizardCampaign?.status !== 'draft'}
                    onPress={() => handleGenerate('sales')}
                  >
                    Generate for sales
                  </Button>
                  <Button
                    color="secondary"
                    isLoading={busy}
                    isDisabled={wizardCampaign?.status !== 'draft'}
                    onPress={() => handleGenerate('quick_demo')}
                  >
                    Generate for quick demo
                  </Button>
                  <Button size="sm" variant="bordered" isLoading={busy} onPress={openLibrary}>
                    Use previous content
                  </Button>
                </div>

                {generatedBatch && generatedBatch.variants?.length > 0 && (
                  <div>
                    <p className="font-semibold text-sm">
                      Generated variants ({generatedBatch.objective}) — model: {generatedBatch.model}
                    </p>
                    {renderVariantCards(generatedBatch.variants)}
                  </div>
                )}

                {wizardCampaign?.subject && (
                  <p className="text-xs text-success">
                    Current subject: {wizardCampaign.subject}
                  </p>
                )}
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>
                  Close
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      <Modal isOpen={libraryModal.isOpen} onOpenChange={libraryModal.onOpenChange} size="3xl" scrollBehavior="inside">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Previous generated content</ModalHeader>
              <ModalBody className="gap-3 max-h-[60vh] overflow-y-auto">
                {libraryItems.length === 0 ? (
                  <p className="text-default-500">No saved variants yet.</p>
                ) : (
                  libraryItems.map((v) => (
                    <Card key={v.id} className="border border-divider">
                      <CardBody className="gap-2 p-3">
                        <p className="text-xs text-default-500">
                          {v.batch_objective} · {v.campaign_name || 'Library'} ·{' '}
                          {formatRegionalDate(v.batch_created_at)}
                        </p>
                        <p className="font-semibold text-sm">{v.subject}</p>
                        <p className="text-xs">{stripHtml(v.body_html, 80)}</p>
                        <Button size="sm" color="primary" isLoading={busy} onPress={() => handleApplyVariant(v)}>
                          Use this
                        </Button>
                      </CardBody>
                    </Card>
                  ))
                )}
              </ModalBody>
              <ModalFooter>
                <Button onPress={onClose}>Close</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      <Modal isOpen={sendModal.isOpen} onOpenChange={sendModal.onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Send campaign</ModalHeader>
              <ModalBody>
                <p>
                  Send to <strong>{selected?.total_recipients}</strong> recipients? Requires Celery worker.
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
                      'Campaign send started.',
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
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml(previewHtml) }}
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
