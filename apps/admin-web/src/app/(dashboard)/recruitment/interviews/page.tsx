'use client';

import React, { useMemo, useState } from 'react';
import {
  Card,
  CardBody,
  Tab,
  Tabs,
  Button,
  Table,
  TableHeader,
  TableBody,
  TableColumn,
  TableRow,
  TableCell,
  Chip,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
  Checkbox,
  Spinner,
} from '@nextui-org/react';
import { Calendar, Mail, Video, Link as LinkIcon, Send, Copy, Plus, Rocket, FileText } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { recruitmentApi, unwrapList } from '@/lib/hrmsApi';
import { CreateCampaignModal } from '@/components/recruitment/CreateCampaignModal';
import { InterviewSettingsCard } from '@/components/recruitment/InterviewSettingsCard';
import { DateTimePickerApply } from '@/components/forms/DateTimePickerApply';
import { validateNumber } from '@/lib/validation';
import axios from 'axios';

type Campaign = {
  id: string;
  title: string;
  status: string;
  job_title?: string;
  stats?: {
    total_candidates: number;
    sent: number;
    above_threshold: number;
    matched: number;
  };
};

type MatchBreakdown = {
  strengths?: string[];
  weaknesses?: string[];
  skills_met?: string[];
  skills_missed?: string[];
  recommendation?: string;
};

type Candidate = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  job_title?: string;
  ai_match_score?: number | null;
  match_passed?: boolean;
  has_active_session?: boolean;
  has_interview_scheduled?: boolean;
  resume_parse_status?: string;
  outreach_status?: string;
  campaign?: string;
  match_breakdown?: MatchBreakdown;
};

type AiSession = {
  id: string;
  candidate: string;
  candidate_name?: string;
  job_title?: string;
  status: string;
  expires_at?: string | null;
  magic_link?: string;
  invite_sent_at?: string | null;
  report_id?: string | null;
  proctor_flags?: { scheduled_at?: string };
};

function apiError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const d = err.response?.data;
    if (typeof d === 'object' && d) {
      if ('error' in d && typeof d.error === 'string') return d.error;
      if ('detail' in d && typeof d.detail === 'string') return d.detail;
    }
  }
  return 'Request failed.';
}

function formatScheduled(session: AiSession): string {
  const raw = session.proctor_flags?.scheduled_at;
  if (raw) {
    try {
      return new Date(raw).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
    } catch {
      return raw;
    }
  }
  if (session.invite_sent_at) {
    return new Date(session.invite_sent_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  }
  return '—';
}

function statusColor(status: string): 'default' | 'primary' | 'success' | 'warning' | 'danger' {
  if (status === 'completed' || status === 'voice_passed' || status === 'sent') return 'success';
  if (status === 'pending' || status === 'active' || status === 'sending') return 'primary';
  if (status === 'expired' || status === 'failed') return 'danger';
  return 'warning';
}

function outreachLabel(status?: string): string {
  if (!status) return '—';
  return status.replace(/_/g, ' ');
}

export default function InterviewSchedulingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [campaignModalOpen, setCampaignModalOpen] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [ccHrAdmin, setCcHrAdmin] = useState(true);
  const [magicLink, setMagicLink] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [modalError, setModalError] = useState('');
  const [scheduledAt, setScheduledAt] = useState<Date | null>(null);
  const [expiryMinutes, setExpiryMinutes] = useState('120');
  const [scheduleError, setScheduleError] = useState('');
  const [expiryError, setExpiryError] = useState('');
  const [includeAssessment, setIncludeAssessment] = useState(false);
  const [launchingId, setLaunchingId] = useState<string | null>(null);
  const [tab, setTab] = useState('campaigns');

  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ['recruitment-campaigns'] });
    queryClient.invalidateQueries({ queryKey: ['recruitment-campaign-candidates'] });
    queryClient.invalidateQueries({ queryKey: ['recruitment-ai-sessions'] });
  };

  const { data: campaigns = [], isLoading: loadingCampaigns } = useQuery({
    queryKey: ['recruitment-campaigns'],
    queryFn: async () => {
      const res = await recruitmentApi.campaigns.list();
      return unwrapList<Campaign>(res.data);
    },
  });

  const { data: candidates = [], isLoading: loadingCandidates } = useQuery({
    queryKey: ['recruitment-campaign-candidates', selectedCampaignId],
    queryFn: async () => {
      const params = selectedCampaignId ? { campaign: selectedCampaignId } : undefined;
      const res = await recruitmentApi.candidates.list(params);
      return unwrapList<Candidate>(res.data);
    },
  });

  const { data: sessions = [], isLoading: loadingSessions } = useQuery({
    queryKey: ['recruitment-ai-sessions'],
    queryFn: async () => {
      const res = await recruitmentApi.aiSessions.list();
      return unwrapList<AiSession>(res.data);
    },
  });

  const campaignCandidates = useMemo(() => {
    if (!selectedCampaignId) return candidates.filter((c) => c.campaign);
    return candidates;
  }, [candidates, selectedCampaignId]);

  const handleLaunch = async (id: string) => {
    setLaunchingId(id);
    try {
      await recruitmentApi.campaigns.launch(id);
      refreshAll();
    } finally {
      setLaunchingId(null);
    }
  };

  const handleOpenSchedule = (candidate: Candidate) => {
    setSelectedCandidate(candidate);
    setMagicLink('');
    setModalError('');
    setScheduledAt(null);
    setExpiryMinutes('120');
    setIncludeAssessment(false);
    setScheduleError('');
    setExpiryError('');
    setScheduleModalOpen(true);
  };

  const renderMatchCell = (item: Candidate) => {
    if (item.resume_parse_status === 'processing' || item.resume_parse_status === 'pending') {
      return (
        <Chip size="sm" color="primary" variant="flat">
          Parsing…
        </Chip>
      );
    }
    if (item.resume_parse_status === 'failed') {
      return (
        <Chip size="sm" color="danger" variant="flat">
          Parse failed
        </Chip>
      );
    }
    if (item.ai_match_score != null && item.ai_match_score >= 0) {
      return (
        <div className="flex flex-col gap-1">
          <Chip
            size="sm"
            color={item.match_passed ? 'success' : 'warning'}
            variant="flat"
          >
            {item.ai_match_score}%
          </Chip>
          {item.match_breakdown?.skills_met?.length ? (
            <p className="text-xs text-default-400 line-clamp-2" title={item.match_breakdown.skills_met.join(', ')}>
              {item.match_breakdown.skills_met.slice(0, 3).join(' · ')}
            </p>
          ) : null}
        </div>
      );
    }
    return <span className="text-default-400">—</span>;
  };

  const canScheduleInterview = (item: Candidate) =>
    Boolean(item.match_passed) &&
    !item.has_interview_scheduled &&
    !item.has_active_session &&
    (item.ai_match_score ?? 0) >= 70;

  const interviewAlreadyScheduled = (item: Candidate) =>
    Boolean(item.has_interview_scheduled || item.has_active_session);

  const handleSendInvite = async () => {
    if (!selectedCandidate) return;
    const schedErr = scheduledAt ? undefined : 'Scheduled time is required.';
    const expErr = validateNumber(expiryMinutes, { min: 15, max: 10080, label: 'Link expiry' });
    setScheduleError(schedErr ?? '');
    setExpiryError(expErr ?? '');
    if (schedErr || expErr) return;

    setIsSending(true);
    setModalError('');
    try {
      const res = await recruitmentApi.candidates.invite(selectedCandidate.id, {
        send_email: true,
        expiry_minutes: parseInt(expiryMinutes, 10),
        scheduled_at: scheduledAt!.toISOString(),
        scheduled_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        cc_hr_admin: ccHrAdmin,
        include_assessment: includeAssessment,
      });
      setMagicLink(res.data.magic_link);
      refreshAll();
    } catch (err) {
      setModalError(apiError(err));
    } finally {
      setIsSending(false);
    }
  };

  const tabLoading =
    (tab === 'campaigns' && loadingCampaigns) ||
    (tab === 'candidates' && loadingCandidates) ||
    (tab === 'sessions' && loadingSessions);

  const renderTabPanel = () => {
    if (tabLoading) {
      return (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      );
    }
    if (tab === 'campaigns') {
      return (
        <Table
          aria-label="Campaigns"
          removeWrapper
          selectionMode="single"
          selectedKeys={selectedCampaignId ? [selectedCampaignId] : []}
          onSelectionChange={(keys) => {
            const id = Array.from(keys)[0] as string | undefined;
            setSelectedCampaignId(id || null);
            if (id) setTab('candidates');
          }}
          classNames={{ wrapper: 'w-full min-w-full', table: 'w-full' }}
        >
          <TableHeader>
            <TableColumn>TITLE</TableColumn>
            <TableColumn>STATUS</TableColumn>
            <TableColumn>CANDIDATES</TableColumn>
            <TableColumn>SENT</TableColumn>
            <TableColumn>MATCH ≥70%</TableColumn>
            <TableColumn align="center">ACTIONS</TableColumn>
          </TableHeader>
          <TableBody emptyContent="No campaigns yet. Create one to get started.">
            {campaigns.map((c) => (
              <TableRow key={c.id}>
                <TableCell className="font-bold">{c.title}</TableCell>
                <TableCell>
                  <Chip size="sm" color={statusColor(c.status)} variant="flat" className="capitalize">
                    {c.status}
                  </Chip>
                </TableCell>
                <TableCell>{c.stats?.total_candidates ?? 0}</TableCell>
                <TableCell>{c.stats?.sent ?? 0}</TableCell>
                <TableCell>{c.stats?.above_threshold ?? 0}</TableCell>
                <TableCell>
                  <div className="flex justify-center gap-2">
                    {(c.status === 'draft' || c.status === 'paused') && (
                      <Button
                        size="sm"
                        color="secondary"
                        variant="flat"
                        isLoading={launchingId === c.id}
                        startContent={<Rocket size={14} />}
                        onPress={() => handleLaunch(c.id)}
                      >
                        Launch emails
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
    }
    if (tab === 'candidates') {
      return (
        <>
          {!selectedCampaignId && (
            <p className="px-4 pt-4 text-sm text-default-500">
              Select a campaign on the Campaigns tab to filter candidates, or view all campaign
              candidates below.
            </p>
          )}
          <Table
            aria-label="Campaign candidates"
            removeWrapper
            classNames={{ wrapper: 'w-full min-w-full', table: 'w-full' }}
          >
            <TableHeader>
              <TableColumn>CANDIDATE</TableColumn>
              <TableColumn>ROLE</TableColumn>
              <TableColumn>MATCH</TableColumn>
              <TableColumn>OUTREACH</TableColumn>
              <TableColumn align="center">ACTIONS</TableColumn>
            </TableHeader>
            <TableBody emptyContent="Select a campaign or create candidates via a new campaign.">
              {campaignCandidates.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-bold">
                    {item.first_name} {item.last_name}
                    <p className="text-xs text-default-400 font-normal">{item.email}</p>
                  </TableCell>
                  <TableCell>{item.job_title || '—'}</TableCell>
                  <TableCell>{renderMatchCell(item)}</TableCell>
                  <TableCell className="capitalize text-sm">{outreachLabel(item.outreach_status)}</TableCell>
                  <TableCell>
                    <div className="flex justify-center">
                      {canScheduleInterview(item) ? (
                        <Button
                          size="sm"
                          color="primary"
                          variant="flat"
                          className="font-bold"
                          startContent={<Calendar size={14} />}
                          onPress={() => handleOpenSchedule(item)}
                        >
                          Schedule interview
                        </Button>
                      ) : interviewAlreadyScheduled(item) ? (
                        <Button
                          size="sm"
                          variant="flat"
                          isDisabled
                          className="opacity-60"
                          startContent={<Calendar size={14} />}
                        >
                          Interview scheduled
                        </Button>
                      ) : item.ai_match_score != null && !item.match_passed ? (
                        <Chip size="sm" color="warning" variant="flat">
                          Below threshold
                        </Chip>
                      ) : null}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      );
    }
    return (
      <Table
        aria-label="AI interview sessions"
        removeWrapper
        classNames={{ wrapper: 'w-full min-w-full', table: 'w-full' }}
      >
        <TableHeader>
          <TableColumn>CANDIDATE</TableColumn>
          <TableColumn>ROLE</TableColumn>
          <TableColumn>STATUS</TableColumn>
          <TableColumn>SCHEDULED / INVITED</TableColumn>
          <TableColumn align="center">ACTIONS</TableColumn>
        </TableHeader>
        <TableBody emptyContent="No interview sessions yet.">
          {sessions.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="font-bold">{item.candidate_name || '—'}</TableCell>
              <TableCell>{item.job_title || '—'}</TableCell>
              <TableCell>
                <Chip size="sm" color={statusColor(item.status)} variant="flat" className="capitalize">
                  {item.status.replace(/_/g, ' ')}
                </Chip>
              </TableCell>
              <TableCell>{formatScheduled(item)}</TableCell>
              <TableCell>
                <div className="flex flex-wrap justify-center gap-2">
                  {item.report_id && (
                    <Button
                      size="sm"
                      color="primary"
                      variant="flat"
                      startContent={<FileText size={14} />}
                      onPress={() => router.push(`/recruitment/ai-interviews/${item.report_id}`)}
                    >
                      View report
                    </Button>
                  )}
                  {(item.status === 'active' || item.status === 'pending') && (
                    <Button
                      size="sm"
                      color="danger"
                      variant="flat"
                      startContent={<Video size={14} />}
                      onPress={() => router.push(`/recruitment/interviews/${item.id}/live`)}
                    >
                      Watch live
                    </Button>
                  )}
                  {item.magic_link && (
                    <Button
                      size="sm"
                      variant="flat"
                      startContent={<Copy size={14} />}
                      onPress={() => navigator.clipboard.writeText(item.magic_link!)}
                    >
                      Copy link
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  };

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-end mb-2">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-extrabold text-foreground">AI Interviews & Scheduling</h1>
          <p className="text-default-500 text-lg">
            Create campaigns, send outreach, and schedule AI interviews when candidates match.
          </p>
        </div>
        <Button color="primary" startContent={<Plus size={18} />} onPress={() => setCampaignModalOpen(true)}>
          Create campaign
        </Button>
      </div>

      <InterviewSettingsCard />

      <Tabs
        aria-label="Interview scheduling sections"
        selectedKey={tab}
        onSelectionChange={(k) => setTab(String(k))}
        classNames={{ tabList: 'gap-4' }}
      >
        <Tab key="campaigns" title="Campaigns" />
        <Tab key="candidates" title="Campaign candidates" />
        <Tab key="sessions" title="AI interview sessions" />
      </Tabs>

      <Card className="shadow-sm border border-divider">
        <CardBody className="p-0">{renderTabPanel()}</CardBody>
      </Card>

      <CreateCampaignModal
        isOpen={campaignModalOpen}
        onOpenChange={setCampaignModalOpen}
        onCreated={refreshAll}
      />

      <Modal isOpen={scheduleModalOpen} onOpenChange={setScheduleModalOpen} size="md">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Schedule AI interview</ModalHeader>
              <ModalBody className="gap-4">
                <p className="text-sm text-default-500">
                  Send interview invite to{' '}
                  <b>
                    {selectedCandidate?.first_name} {selectedCandidate?.last_name}
                  </b>{' '}
                  (match {selectedCandidate?.ai_match_score}%).
                </p>
                <DateTimePickerApply
                  label="Scheduled time"
                  value={scheduledAt}
                  onChange={setScheduledAt}
                  isRequired
                  errorMessage={scheduleError}
                />
                <Input
                  type="number"
                  label="Link expiry (minutes)"
                  variant="bordered"
                  value={expiryMinutes}
                  onValueChange={setExpiryMinutes}
                  errorMessage={expiryError}
                  isInvalid={!!expiryError}
                />
                <Checkbox isSelected={ccHrAdmin} onValueChange={setCcHrAdmin}>
                  CC me (HR admin)
                </Checkbox>
                <Checkbox isSelected={includeAssessment} onValueChange={setIncludeAssessment}>
                  Include online assessment after voice interview
                </Checkbox>
                <p className="text-xs text-default-400">
                  Assessment is only sent to the candidate when this box is checked. Job-level assessment
                  settings do not auto-include it.
                </p>
                {modalError && <p className="text-danger text-sm">{modalError}</p>}
                {magicLink && (
                  <div className="p-3 bg-success/10 border border-success/30 rounded-xl">
                    <p className="text-xs break-all">{magicLink}</p>
                  </div>
                )}
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>
                  Close
                </Button>
                {!magicLink ? (
                  <Button color="primary" isLoading={isSending} onPress={handleSendInvite}>
                    Send invite
                  </Button>
                ) : (
                  <Button color="success" onPress={onClose}>
                    Done
                  </Button>
                )}
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
