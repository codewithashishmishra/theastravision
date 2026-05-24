'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button, Card, CardBody, Progress, Spinner } from '@nextui-org/react';
import { Mic, MicOff } from 'lucide-react';
import publicApi from '@/lib/publicApi';

type QuestionPayload = {
  done: boolean;
  question?: { id: string; order: number; question_text: string };
  index?: number;
  total?: number;
  tts_audio_base64?: string | null;
  tts_mime?: string;
};

export default function InterviewLivePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState<QuestionPayload | null>(null);
  const [recording, setRecording] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lastScore, setLastScore] = useState<number | null>(null);
  const [error, setError] = useState('');
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const loadQuestion = useCallback(async () => {
    const res = await publicApi.get<QuestionPayload>(
      `/recruitment/ai-sessions/${sessionId}/questions/next/`,
    );
    setQuestion(res.data);
    if (res.data.tts_audio_base64) {
      const mime = res.data.tts_mime || 'audio/mpeg';
      const audio = new Audio(`data:${mime};base64,${res.data.tts_audio_base64}`);
      audio.play().catch(() => undefined);
    }
    setLoading(false);
  }, [sessionId]);

  useEffect(() => {
    loadQuestion().catch(() => setError('Failed to load question.'));
  }, [loadQuestion]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunks.current = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.current.push(e.data);
    };
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunks.current, { type: 'audio/webm' });
      await submitAnswer(blob);
    };
    mediaRecorder.current = recorder;
    recorder.start();
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorder.current?.stop();
    setRecording(false);
  };

  const submitAnswer = async (blob: Blob) => {
    if (!question?.question) return;
    setSubmitting(true);
    const form = new FormData();
    form.append('question_id', question.question.id);
    form.append('audio', blob, 'answer.webm');
    try {
      const res = await publicApi.post(`/recruitment/ai-sessions/${sessionId}/answers/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setLastScore(res.data.score_percent ?? null);
      setLoading(true);
      await loadQuestion();
    } catch {
      setError('Failed to submit answer.');
    } finally {
      setSubmitting(false);
    }
  };

  const finishInterview = async () => {
    const res = await publicApi.post(`/recruitment/ai-sessions/${sessionId}/complete-voice/`);
    if (res.data.assessment_link) {
      const token = res.data.assessment_link.split('/').pop();
      router.push(`/assessment/${token}`);
    } else {
      router.push(`/interview/complete?passed=${res.data.passed}`);
    }
  };

  if (error) {
    return <div className="flex min-h-screen items-center justify-center text-danger">{error}</div>;
  }

  if (loading && !question) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (question?.done) {
    return (
      <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-6 p-6">
        <Card className="bg-slate-800/60">
          <CardBody className="gap-4 p-8 text-center">
            <h2 className="text-2xl font-bold">Voice interview complete</h2>
            <p className="text-default-400">Submit to see your result and next steps.</p>
            <Button color="primary" size="lg" onPress={finishInterview}>
              Finish & continue
            </Button>
          </CardBody>
        </Card>
      </div>
    );
  }

  const progress = question?.total ? ((question.index || 1) / question.total) * 100 : 0;

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase text-violet-400">Astra is listening</p>
          <h1 className="text-2xl font-bold">Question {question?.index} of {question?.total}</h1>
        </div>
        {lastScore !== null && (
          <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-sm text-emerald-300">
            Last: {Math.round(lastScore)}%
          </span>
        )}
      </div>
      <Progress value={progress} color="secondary" className="max-w-full" />
      <Card className="bg-slate-800/60 border border-violet-500/20">
        <CardBody className="gap-6 p-8">
          <p className="text-xl leading-relaxed">{question?.question?.question_text}</p>
          <div className="flex flex-col items-center gap-4">
            <Button
              color={recording ? 'danger' : 'primary'}
              size="lg"
              className="w-full max-w-xs font-bold"
              startContent={recording ? <MicOff size={20} /> : <Mic size={20} />}
              isLoading={submitting}
              onPress={recording ? stopRecording : startRecording}
            >
              {recording ? 'Stop & submit answer' : 'Hold to record answer'}
            </Button>
            <p className="text-center text-xs text-default-500">
              Speak clearly in English or Hindi. Astra evaluates in English.
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
