'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card,
  CardBody,
  Button,
  Chip,
  Avatar,
  Spinner,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Textarea,
} from '@nextui-org/react';
import {
  MessageSquare,
  Bot,
  User,
  Activity,
  AlertTriangle,
  Share2,
  Mic,
} from 'lucide-react';
import { recruitmentApi } from '@/lib/hrmsApi';
import { getAccessToken } from '@/lib/tokenStore';
import { useInterviewLiveSocket } from '@/lib/useInterviewLiveSocket';
import { useInterviewMsePlayer } from '@/lib/useInterviewMsePlayer';

type LiveSessionInfo = {
  id: string;
  status: string;
  candidate_name: string;
  job_title: string;
  current_question_index: number;
  current_question_text: string | null;
  recording_started_at: string | null;
  live_watch_enabled: boolean;
};

export default function AIInterviewLivePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [session, setSession] = useState<LiveSessionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [flagOpen, setFlagOpen] = useState(false);
  const [flagNote, setFlagNote] = useState('');
  const [terminating, setTerminating] = useState(false);
  const transcriptRef = useRef<HTMLDivElement>(null);

  const token = typeof window !== 'undefined' ? getAccessToken() : null;
  const { transcript, connected, lastChunk, sessionEnded, setTranscript } = useInterviewLiveSocket(
    id,
    token,
    'hr',
  );
  const {
    videoRef: screenVideoRef,
    appendChunk,
    latencyMs,
    error: playerError,
  } = useInterviewMsePlayer(id, 'session_composite');

  const loadSession = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await recruitmentApi.aiSessions.getLive(id);
      setSession(res.data as LiveSessionInfo);
      if (res.data.current_question_text) {
        setTranscript([
          {
            sender: 'AI',
            text: res.data.current_question_text,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    } catch {
      setError('Could not load live session.');
    } finally {
      setLoading(false);
    }
  }, [id, setTranscript]);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  useEffect(() => {
    if (lastChunk?.kind === 'session_composite') {
      void appendChunk(lastChunk.sequence, lastChunk.created_at);
    }
  }, [lastChunk, appendChunk]);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript]);

  const handleTerminate = async () => {
    if (!id || !confirm('Terminate this interview session?')) return;
    setTerminating(true);
    try {
      await recruitmentApi.aiSessions.terminate(id);
      router.push('/recruitment/interviews');
    } catch {
      setError('Failed to terminate session.');
    } finally {
      setTerminating(false);
    }
  };

  const handleFlag = async () => {
    if (!id) return;
    try {
      await recruitmentApi.aiSessions.flagConcern(id, flagNote || undefined);
      setFlagOpen(false);
      setFlagNote('');
    } catch {
      setError('Failed to flag concern.');
    }
  };

  const isLive = session?.status === 'active' && !sessionEnded;

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <p className="text-danger">{error || 'Session not found'}</p>
        <Button onPress={() => router.push('/recruitment/interviews')}>Back</Button>
      </div>
    );
  }

  if (!session.live_watch_enabled) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <p className="text-default-500">Live watch is disabled for this organization.</p>
        <Button onPress={() => router.push('/recruitment/interviews')}>Back</Button>
      </div>
    );
  }

  return (
    <div className="flex h-[85vh] w-full flex-col gap-6">
      <div className="flex shrink-0 items-center justify-between rounded-3xl border border-divider bg-content1 p-4 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Avatar name={session.candidate_name} size="lg" className="ring-2 ring-primary/20" />
            {isLive && (
              <span className="absolute bottom-0 right-0 h-4 w-4 animate-pulse rounded-full border-2 border-content1 bg-danger" />
            )}
          </div>
          <div>
            <h1 className="flex items-center gap-2 text-xl font-extrabold text-foreground">
              {session.candidate_name}
              {isLive && (
                <Chip size="sm" color="danger" variant="flat" className="ml-2 animate-pulse font-bold">
                  LIVE AI INTERVIEW
                </Chip>
              )}
              {!isLive && (
                <Chip size="sm" variant="flat" color="default">
                  {session.status}
                </Chip>
              )}
            </h1>
            <p className="text-sm font-medium text-default-500">
              {session.job_title}
              {connected ? ' • Connected' : ' • Reconnecting…'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="flat"
            startContent={<AlertTriangle size={18} />}
            color="warning"
            onPress={() => setFlagOpen(true)}
            isDisabled={!isLive}
          >
            Flag Concern
          </Button>
          <Button
            color="danger"
            className="font-bold shadow-lg shadow-danger/30"
            onPress={handleTerminate}
            isLoading={terminating}
            isDisabled={!isLive}
          >
            Terminate Session
          </Button>
        </div>
      </div>

      <div className="flex flex-1 gap-6 overflow-hidden">
        <div className="flex min-w-[600px] flex-[3] flex-col gap-6">
          <Card className="group relative flex-1 overflow-hidden rounded-3xl border border-divider/20 bg-black shadow-2xl">
            <video
              ref={screenVideoRef}
              className="h-full w-full object-contain"
              muted
              playsInline
              autoPlay
            />
            {!isLive && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/70 text-default-300">
                Session not active
              </div>
            )}
            {playerError && (
              <div className="absolute bottom-4 left-4 rounded bg-danger/80 px-3 py-1 text-xs text-white">
                {playerError}
              </div>
            )}
            <div className="absolute bottom-6 left-6 z-10 flex aspect-video w-48 items-center justify-center overflow-hidden rounded-xl border-2 border-divider bg-content2 shadow-2xl">
              <div className="flex flex-col items-center gap-2 text-default-400">
                <User size={32} />
                <span className="text-xs">Camera in composite</span>
              </div>
              <div className="absolute bottom-2 left-2 flex items-center gap-2 rounded bg-black/60 px-2 py-1 text-xs text-white backdrop-blur-md">
                <Mic size={12} className="text-success" />
                {session.candidate_name.split(' ')[0]}
              </div>
            </div>
            <div className="absolute right-6 top-6 flex gap-2">
              <div className="flex items-center gap-2 rounded-lg bg-black/60 px-3 py-1.5 text-xs font-bold text-white backdrop-blur-md">
                <Activity size={14} className="text-danger" />
                {latencyMs != null ? `${latencyMs}ms delay` : '—'}
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-black/60 px-3 py-1.5 text-xs text-white backdrop-blur-md">
                <Share2 size={14} />
                Live
              </div>
            </div>
          </Card>
        </div>

        <div className="flex min-w-[400px] flex-[2] flex-col gap-6">
          <Card className="flex flex-1 flex-col border border-divider shadow-sm">
            <div className="flex shrink-0 items-center justify-between border-b border-divider bg-default-50/50 p-4">
              <h3 className="flex items-center gap-2 font-bold">
                <MessageSquare size={18} className="text-primary" />
                Live Transcript
              </h3>
              <Chip size="sm" variant="flat" color={isLive ? 'success' : 'default'}>
                {isLive ? 'Recording Active' : 'Ended'}
              </Chip>
            </div>
            <CardBody
              className="custom-scrollbar flex flex-col gap-4 overflow-y-auto p-6"
              ref={transcriptRef}
            >
              {transcript.length === 0 && (
                <p className="text-center text-sm text-default-400">Waiting for conversation…</p>
              )}
              {transcript.map((msg, i) => (
                <div
                  key={i}
                  className={`flex max-w-[90%] gap-3 ${msg.sender === 'Candidate' ? 'ml-auto flex-row-reverse' : ''}`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      msg.sender === 'AI' ? 'bg-primary/20 text-primary' : 'bg-success/20 text-success'
                    }`}
                  >
                    {msg.sender === 'AI' ? <Bot size={16} /> : <User size={16} />}
                  </div>
                  <div className={`flex flex-col ${msg.sender === 'Candidate' ? 'items-end' : ''}`}>
                    <span className="mb-1 px-1 text-[11px] font-medium text-default-400">
                      {msg.sender} • {msg.time}
                    </span>
                    <div
                      className={`rounded-2xl p-3 text-[14px] leading-relaxed shadow-sm ${
                        msg.sender === 'Candidate'
                          ? 'border border-divider bg-content2 text-foreground'
                          : 'border border-primary/20 bg-primary/10 text-primary-800'
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>
        </div>
      </div>

      <Modal isOpen={flagOpen} onOpenChange={setFlagOpen}>
        <ModalContent>
          <ModalHeader>Flag concern</ModalHeader>
          <ModalBody>
            <Textarea
              label="Note"
              placeholder="Describe the concern for HR review…"
              value={flagNote}
              onValueChange={setFlagNote}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="flat" onPress={() => setFlagOpen(false)}>
              Cancel
            </Button>
            <Button color="warning" onPress={handleFlag}>
              Submit
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
