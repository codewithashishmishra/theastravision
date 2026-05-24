'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button, Card, CardBody, Checkbox, Spinner } from '@nextui-org/react';
import publicApi from '@/lib/publicApi';

type SessionInfo = {
  id: string;
  candidate_name: string;
  job_title: string;
  expires_at: string;
  question_count: number;
  assessment_enabled: boolean;
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
      .catch((err) => setError(err.response?.data?.error || 'Invalid or expired link.'))
      .finally(() => setLoading(false));
  }, [token]);

  const handleStart = async () => {
    if (!info || !consent) return;
    setStarting(true);
    try {
      await publicApi.post(`/recruitment/ai-sessions/${info.id}/start/`);
      router.push(`/interview/${info.id}/live`);
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
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-8 p-6">
      <div className="text-center">
        <p className="text-sm uppercase tracking-widest text-violet-400">AastraaHR</p>
        <h1 className="mt-2 text-3xl font-bold">Meet Astra</h1>
        <p className="mt-2 text-default-400">AI voice interview for {info.job_title}</p>
      </div>
      <Card className="bg-slate-800/60 border border-white/10">
        <CardBody className="gap-6 p-8">
          <p className="text-lg">
            Hello <strong>{info.candidate_name}</strong>, Astra will ask you about{' '}
            <strong>{info.question_count}</strong> topics based on your profile and the role.
          </p>
          <ul className="list-disc space-y-2 pl-5 text-sm text-default-400">
            <li>Astra speaks in English (Indian accent).</li>
            <li>You may answer in <strong>English or Hindi</strong>; answers are evaluated in English.</li>
            <li>Use a quiet room and allow microphone access.</li>
            {info.assessment_enabled && (
              <li>After the voice interview, you may complete a proctored online assessment.</li>
            )}
          </ul>
          <Checkbox isSelected={consent} onValueChange={setConsent} classNames={{ label: 'text-sm' }}>
            I consent to recording my voice for this interview.
          </Checkbox>
          <Button
            color="primary"
            size="lg"
            className="font-bold"
            isDisabled={!consent}
            isLoading={starting}
            onPress={handleStart}
          >
            Start interview with Astra
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}
