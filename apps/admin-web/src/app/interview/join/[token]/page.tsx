'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button, Card, CardBody, Checkbox, Spinner } from '@nextui-org/react';
import publicApi from '@/lib/publicApi';
import { setInterviewMagicToken } from '@/lib/interviewLiveUpload';
import { AstraAvatar, InterviewShell } from '@/components/interview/InterviewShell';

type SessionInfo = {
  id: string;
  candidate_name: string;
  job_title: string;
  expires_at: string;
  question_count: number;
  include_assessment: boolean;
};

export default function InterviewJoinPage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const [info, setInfo] = useState<SessionInfo | null>(null);
  const [error, setError] = useState('');
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    publicApi
      .get(`/recruitment/ai-sessions/verify/${token}/`)
      .then((res) => setInfo(res.data))
      .catch((err) => {
        const status = err.response?.status;
        const msg = err.response?.data?.error;
        if (status === 404) {
          setError('This interview link is invalid. Check that you copied the full URL from your invite email.');
        } else if (status === 403) {
          setError(msg || 'This interview link has expired. Ask HR to send a new invite.');
        } else if (status === 428) {
          setError('Secure connection could not be established. Refresh the page or try another browser.');
        } else {
          setError(msg || 'Unable to verify this interview link. Try again or contact HR.');
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  const handleStart = async () => {
    if (!info || !consent) return;
    setStarting(true);
    try {
      setInterviewMagicToken(info.id, token);
      router.push(`/interview/${info.id}/preflight`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      setError(e.response?.data?.error || 'Could not start interview.');
    } finally {
      setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  if (error || !info) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <Card className="max-w-md bg-slate-800/80">
          <CardBody className="gap-4 p-8 text-center">
            <h1 className="text-xl font-bold text-danger">Unable to join</h1>
            <p className="text-default-400">{error}</p>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <InterviewShell step={1} subtitle={`AI voice interview — ${info.job_title}`}>
      <Card className="border border-white/10 bg-slate-800/80">
        <CardBody className="gap-6 p-8">
          <AstraAvatar />
          <h1 className="text-center text-2xl font-bold">Meet Astra</h1>
          <p className="text-center text-slate-400">
            Hello <strong>{info.candidate_name}</strong>, your virtual interviewer will guide you through{' '}
            <strong>{info.question_count}</strong> voice questions tailored to this role.
          </p>
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-400">
            <li>Astra will speak each question aloud (English).</li>
            <li>You may answer in <strong>English or Hindi</strong>; responses are evaluated in English.</li>
            <li>Next you will enable camera, screen share, and microphone.</li>
            {info.include_assessment && (
              <li>After the voice interview, you may complete a short online assessment.</li>
            )}
          </ul>
          <Checkbox isSelected={consent} onValueChange={setConsent} classNames={{ label: 'text-sm' }}>
            I consent to voice, video, and screen recording for this interview.
          </Checkbox>
          <Button
            color="primary"
            size="lg"
            className="w-full font-bold"
            isDisabled={!consent}
            isLoading={starting}
            onPress={handleStart}
          >
            Continue to setup
          </Button>
        </CardBody>
      </Card>
    </InterviewShell>
  );
}
