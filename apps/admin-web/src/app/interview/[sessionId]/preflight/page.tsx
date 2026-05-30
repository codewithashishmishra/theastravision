'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button, Card, CardBody, Checkbox, Spinner } from '@nextui-org/react';
import { Camera, Mic, Monitor } from 'lucide-react';
import publicApi from '@/lib/publicApi';
import { unlockInterviewAudio } from '@/lib/interviewTts';
import { AstraAvatar, InterviewShell } from '@/components/interview/InterviewShell';

export default function InterviewPreflightPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [cameraOk, setCameraOk] = useState(false);
  const [screenOk, setScreenOk] = useState(false);
  const [micOk, setMicOk] = useState(false);
  const [rulesOk, setRulesOk] = useState(false);
  const [voiceOk, setVoiceOk] = useState(false);
  const [error, setError] = useState('');
  const [continuing, setContinuing] = useState(false);
  const [tabSwitches, setTabSwitches] = useState(0);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === 'hidden') setTabSwitches((n) => n + 1);
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  const tryCamera = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      s.getTracks().forEach((t) => t.stop());
      setCameraOk(true);
    } catch {
      setError('Camera access is required. Check browser permissions.');
    }
  };

  const tryScreen = async () => {
    try {
      const s = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      s.getTracks().forEach((t) => t.stop());
      setScreenOk(true);
    } catch {
      setError('Screen sharing is required for this interview.');
    }
  };

  const tryMic = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });
      s.getTracks().forEach((t) => t.stop());
      setMicOk(true);
    } catch {
      setError('Microphone access is required.');
    }
  };

  const handleContinue = async () => {
    if (!cameraOk || !screenOk || !micOk || !rulesOk || !voiceOk) return;
    setContinuing(true);
    setError('');
    try {
      // Unlock audio in the same tap as Continue (before slow network calls — Safari gesture window).
      await unlockInterviewAudio();
      await publicApi.post(`/recruitment/ai-sessions/${sessionId}/preflight/`, {
        tab_switch_count: tabSwitches,
      });
      await publicApi.post(`/recruitment/ai-sessions/${sessionId}/start/`);
      sessionStorage.setItem(`interview_tab_switches_${sessionId}`, String(tabSwitches));
      router.push(`/interview/${sessionId}/live`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      setError(e.response?.data?.error || 'Could not start interview.');
    } finally {
      setContinuing(false);
    }
  };

  const ready = cameraOk && screenOk && micOk && rulesOk && voiceOk;

  return (
    <InterviewShell step={2} subtitle="Before you begin">
      <Card className="border border-white/10 bg-slate-800/80">
        <CardBody className="gap-6 p-8">
          <AstraAvatar />
          <h1 className="text-center text-2xl font-bold">Prepare for your interview</h1>
          <p className="text-center text-sm text-slate-400">
            Complete each step below. Astra will guide you through voice questions. Your session may be
            recorded for HR review.
          </p>
          <ul className="space-y-3 text-sm text-slate-300">
            <li>• Astra will read these rules aloud when the interview starts.</li>
            <li>• Use a quiet, well-lit room.</li>
            <li>• Answer in English or Hindi (evaluated in English).</li>
            <li>• Stay on this tab — do not look away or switch windows unnecessarily.</li>
            <li>• Do not use notes or external help unless HR instructed otherwise.</li>
            <li>• Say &quot;skip this question&quot; if you do not know an answer (3 skips ends the interview).</li>
          </ul>
          <div className="grid gap-3 sm:grid-cols-3">
            <Button
              variant={cameraOk ? 'solid' : 'bordered'}
              color={cameraOk ? 'success' : 'default'}
              startContent={<Camera size={18} />}
              aria-label={cameraOk ? 'Camera ready' : 'Enable camera'}
              onPress={tryCamera}
            >
              {cameraOk ? 'Camera ready' : 'Enable camera'}
            </Button>
            <Button
              variant={screenOk ? 'solid' : 'bordered'}
              color={screenOk ? 'success' : 'default'}
              startContent={<Monitor size={18} />}
              aria-label={screenOk ? 'Screen share ready' : 'Share screen'}
              onPress={tryScreen}
            >
              {screenOk ? 'Screen shared' : 'Share screen'}
            </Button>
            <Button
              variant={micOk ? 'solid' : 'bordered'}
              color={micOk ? 'success' : 'default'}
              startContent={<Mic size={18} />}
              aria-label={micOk ? 'Microphone ready' : 'Enable microphone'}
              onPress={tryMic}
            >
              {micOk ? 'Mic ready' : 'Enable microphone'}
            </Button>
          </div>
          <Checkbox
            isSelected={rulesOk}
            onValueChange={setRulesOk}
            aria-label="I understand and will follow the interview guidelines"
          >
            I understand and will follow the interview guidelines above.
          </Checkbox>
          <Checkbox
            isSelected={voiceOk}
            onValueChange={setVoiceOk}
            aria-label="I agree to hear Astra speak during this interview"
          >
            I agree to hear Astra&apos;s voice during this interview (required for autoplay in your browser).
          </Checkbox>
          {error && <p className="text-center text-sm text-danger">{error}</p>}
          <Button
            color="primary"
            size="lg"
            className="font-bold"
            isDisabled={!ready}
            isLoading={continuing}
            onPress={handleContinue}
          >
            Continue to interview
          </Button>
        </CardBody>
      </Card>
    </InterviewShell>
  );
}
