'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import { Button, Card, CardBody, Radio, RadioGroup, Spinner } from '@nextui-org/react';
import publicApi from '@/lib/publicApi';

type Mcq = {
  id: string;
  order: number;
  prompt: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
};

type AssessmentData = {
  session_id: string;
  duration_minutes: number;
  proctor_interval_seconds: number;
  questions: Mcq[];
};

export default function AssessmentPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<AssessmentData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [cameraOk, setCameraOk] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    publicApi
      .get<AssessmentData>(`/recruitment/assessment/${token}/`)
      .then((res) => {
        setData(res.data);
        setSecondsLeft(res.data.duration_minutes * 60);
      })
      .catch(() => setError('Assessment not available.'));
  }, [token]);

  const enableCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOk(true);
      await publicApi.post(`/recruitment/assessment/${token}/start/`, { camera_active: true });
    } catch {
      setError('Camera is required. Please allow camera access and use a desktop browser if needed.');
    }
  };

  const captureProctor = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || !cameraOk) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const form = new FormData();
      form.append('image', blob, 'proctor.jpg');
      try {
        await publicApi.post(`/recruitment/assessment/${token}/proctor/`, form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } catch {
        /* ignore transient proctor errors */
      }
    }, 'image/jpeg', 0.85);
  }, [cameraOk, token]);

  useEffect(() => {
    if (!cameraOk || !data) return;
    const interval = setInterval(captureProctor, (data.proctor_interval_seconds || 60) * 1000);
    return () => clearInterval(interval);
  }, [cameraOk, data, captureProctor]);

  useEffect(() => {
    if (!cameraOk || secondsLeft <= 0) return;
    const t = setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(t);
  }, [cameraOk, secondsLeft]);

  useEffect(() => {
    if (cameraOk && secondsLeft === 0 && data && !done) {
      handleSubmit();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secondsLeft, cameraOk]);

  const handleSubmit = async () => {
    if (!data || !cameraOk) return;
    setSubmitting(true);
    try {
      const res = await publicApi.post(`/recruitment/assessment/${token}/submit/`, { answers });
      setScore(res.data.score);
      setDone(true);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      setError(e.response?.data?.error || 'Submit failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, '0')}`;
  };

  if (error) {
    return <div className="flex min-h-screen items-center justify-center p-6 text-danger">{error}</div>;
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <Spinner size="lg" />
      </div>
    );
  }

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-white">
        <Card className="max-w-md bg-slate-800">
          <CardBody className="gap-4 p-8 text-center">
            <h1 className="text-2xl font-bold">Assessment submitted</h1>
            <p className="text-3xl font-extrabold text-emerald-400">{Math.round(score ?? 0)}%</p>
            <p className="text-sm text-default-400">HR will receive your full AI interview report by email.</p>
          </CardBody>
        </Card>
      </div>
    );
  }

  if (!cameraOk) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-slate-950 p-6 text-white">
        <h1 className="text-2xl font-bold">Proctored assessment</h1>
        <p className="max-w-md text-center text-default-400">
          Camera must stay on for the full {data.duration_minutes}-minute exam ({data.questions.length}{' '}
          questions).
        </p>
        <video ref={videoRef} className="aspect-video w-full max-w-md rounded-lg bg-black" muted playsInline />
        <Button color="primary" size="lg" onPress={enableCamera}>
          Enable camera & start
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <canvas ref={canvasRef} className="hidden" />
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-slate-900/95 px-6 py-3">
        <span className="font-bold">Online assessment</span>
        <span className={`font-mono text-lg ${secondsLeft < 120 ? 'text-danger' : 'text-emerald-400'}`}>
          {formatTime(secondsLeft)}
        </span>
      </div>
      <div className="mx-auto grid max-w-6xl gap-6 p-6 lg:grid-cols-[280px_1fr]">
        <div className="sticky top-20 h-fit">
          <Card className="bg-slate-800">
            <CardBody className="p-4">
              <p className="mb-2 text-xs text-default-400">Proctor camera</p>
              <video ref={videoRef} className="aspect-video w-full rounded-lg bg-black object-cover" muted playsInline />
            </CardBody>
          </Card>
        </div>
        <div className="flex flex-col gap-8">
          {data.questions.map((q) => (
            <Card key={q.id} className="bg-slate-800/80">
              <CardBody className="gap-4 p-6">
                <p className="font-semibold">
                  {q.order}. {q.prompt}
                </p>
                <RadioGroup
                  value={answers[q.id] || ''}
                  onValueChange={(v) => setAnswers((prev) => ({ ...prev, [q.id]: v }))}
                >
                  <Radio value="A">{q.option_a}</Radio>
                  <Radio value="B">{q.option_b}</Radio>
                  <Radio value="C">{q.option_c}</Radio>
                  <Radio value="D">{q.option_d}</Radio>
                </RadioGroup>
              </CardBody>
            </Card>
          ))}
          <Button
            color="primary"
            size="lg"
            isLoading={submitting}
            isDisabled={Object.keys(answers).length < data.questions.length}
            onPress={handleSubmit}
          >
            Submit assessment
          </Button>
        </div>
      </div>
    </div>
  );
}
