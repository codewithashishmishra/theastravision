'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  AlertTriangle,
  Bug,
  Clock,
  Loader2,
  Mic,
  MicOff,
  Monitor,
  PhoneOff,
  SkipForward,
  Sparkles,
  Video,
  VideoOff,
  Volume2,
  X,
} from 'lucide-react';
import publicApi from '@/lib/publicApi';
import { speakAstra, speakQuestion, unlockInterviewAudio } from '@/lib/interviewTts';
import { listenForAnswer, SkipRequestedError } from '@/lib/interviewListening';
import {
  acquireInterviewMedia,
  releaseInterviewMedia,
  startInterviewRecording,
  type InterviewMediaResult,
} from '@/lib/interviewMedia';
import { createChunkUploader, getInterviewMagicToken } from '@/lib/interviewLiveUpload';
import type { SessionRecorder } from '@/lib/sessionRecorder';
import { SILENCE_NUDGE_SCRIPT } from '@/lib/interviewScripts';

type Phase = 'loading' | 'setup' | 'speaking' | 'listening' | 'processing' | 'done' | 'expired' | 'error';

type QuestionPayload = {
  done: boolean;
  question?: { id: string; order: number; question_text: string };
  index?: number;
  total?: number;
  tts_audio_base64?: string | null;
  tts_mime?: string;
  skip_count?: number;
  include_assessment?: boolean;
};

type SessionMeta = {
  expires_at?: string | null;
  include_assessment?: boolean;
  question_count?: number;
  status?: string;
};

function formatCountdown(secs: number) {
  const s = Math.max(0, secs);
  const mins = Math.floor(s / 60);
  const rem = s % 60;
  return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
}

function statusText(phase: Phase, speaking: boolean) {
  if (phase === 'setup') return 'SETUP REQUIRED';
  if (speaking) return 'ASTRA SPEAKING';
  if (phase === 'listening') return 'LISTENING';
  if (phase === 'processing') return 'PROCESSING RESPONSE';
  if (phase === 'expired') return 'SESSION EXPIRED';
  if (phase === 'error') return 'ACTION REQUIRED';
  if (phase === 'done') return 'INTERVIEW COMPLETE';
  return 'PREPARING';
}

function MediaStreamPreview({ stream, className }: { stream: MediaStream; className?: string }) {
  const ref = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.srcObject = stream;
    void el.play().catch(() => {});
    return () => {
      el.pause();
      el.srcObject = null;
    };
  }, [stream]);
  return <video ref={ref} muted playsInline autoPlay className={className} />;
}

export default function InterviewLivePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();

  const [phase, setPhase] = useState<Phase>('setup');
  const [question, setQuestion] = useState<QuestionPayload | null>(null);
  const [sessionMeta, setSessionMeta] = useState<SessionMeta>({});
  const [remainingSeconds, setRemainingSeconds] = useState(20 * 60);
  const [isAstraSpeaking, setIsAstraSpeaking] = useState(false);
  const [isMicMuted, setIsMicMuted] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [fatalError, setFatalError] = useState('');
  const [showEndModal, setShowEndModal] = useState(false);
  const [showBugModal, setShowBugModal] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [isSubmittingBug, setIsSubmittingBug] = useState(false);
  const [previewScreen, setPreviewScreen] = useState<MediaStream | null>(null);
  const [previewCamera, setPreviewCamera] = useState<MediaStream | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [skipCount, setSkipCount] = useState(0);
  const [recorderWarning, setRecorderWarning] = useState('');
  const [errorHidden, setErrorHidden] = useState(false);
  const [bugTitle, setBugTitle] = useState('');
  const [bugDescription, setBugDescription] = useState('');
  const [bugImage, setBugImage] = useState<File | null>(null);
  const [bugMessage, setBugMessage] = useState('');
  const [bugMessageType, setBugMessageType] = useState<'success' | 'error'>('success');

  const interviewMedia = useRef<InterviewMediaResult | null>(null);
  const listenAbort = useRef<AbortController | null>(null);
  const turnActive = useRef(false);
  const expiredTriggered = useRef(false);
  const sessionRecorder = useRef<SessionRecorder | null>(null);
  const chunkUploader = useRef<ReturnType<typeof createChunkUploader> | null>(null);
  const tabSwitches = useRef(0);

  const siriCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const totalQuestions = question?.total ?? sessionMeta.question_count ?? 0;
  const activeQuestionIndex = question?.index ?? 0;
  const hasRequiredMedia = Boolean(previewCamera && previewScreen);

  const runTurnRef = useRef<() => Promise<void>>(async () => {});
  const consolidatedError = !errorHidden ? (fatalError || voiceError || '') : '';

  useEffect(() => {
    if (!consolidatedError) return;
    const timer = window.setTimeout(() => {
      setFatalError('');
      setVoiceError('');
      setErrorHidden(false);
    }, 7000);
    return () => window.clearTimeout(timer);
  }, [consolidatedError]);

  useEffect(() => {
    if (fatalError || voiceError) setErrorHidden(false);
  }, [fatalError, voiceError]);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === 'hidden') tabSwitches.current += 1;
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setRemainingSeconds((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const uploadRecording = useCallback(async () => {
    if (!sessionRecorder.current) return;
    const { sessionBlob, cameraBlob } = await sessionRecorder.current.stop();
    try {
      await chunkUploader.current?.finalize(tabSwitches.current);
    } catch {
      const form = new FormData();
      form.append('session_video', sessionBlob, 'session.webm');
      if (cameraBlob) form.append('camera_video', cameraBlob, 'camera.webm');
      form.append('tab_switch_count', String(tabSwitches.current));
      await publicApi.post(`/recruitment/ai-sessions/${sessionId}/upload-recording/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    }
  }, [sessionId]);

  const finishInterview = useCallback(
    async (reason?: string) => {
      if (isEnding) return;
      setIsEnding(true);
      listenAbort.current?.abort();
      turnActive.current = false;
      try {
        await uploadRecording();
      } catch {
        /* continue */
      }
      try {
        const res = await publicApi.post(`/recruitment/ai-sessions/${sessionId}/complete-voice/`);
        if (res.data.assessment_link) {
          const token = String(res.data.assessment_link).split('/').pop();
          router.push(`/assessment/${token}`);
          return;
        }
      } catch {
        /* continue */
      }
      router.push(`/interview/complete?sessionId=${sessionId}${reason ? `&reason=${reason}` : ''}`);
    },
    [isEnding, uploadRecording, sessionId, router],
  );

  useEffect(() => {
    if (remainingSeconds > 0 || expiredTriggered.current) return;
    expiredTriggered.current = true;
    setPhase('expired');
    void finishInterview('expired');
  }, [remainingSeconds, finishInterview]);

  const fetchQuestion = useCallback(async (): Promise<QuestionPayload> => {
    const res = await publicApi.get<QuestionPayload>(`/recruitment/ai-sessions/${sessionId}/questions/next/`);
    setQuestion(res.data);
    if (res.data.skip_count !== undefined) setSkipCount(res.data.skip_count);
    if (res.data.include_assessment !== undefined) {
      setSessionMeta((prev) => ({ ...prev, include_assessment: res.data.include_assessment }));
    }
    return res.data;
  }, [sessionId]);

  const playCurrentQuestion = useCallback(
    async (payload: QuestionPayload) => {
      if (!payload.question?.question_text) return;
      setIsAstraSpeaking(true);
      setPhase('speaking');
      setVoiceError('');
      await unlockInterviewAudio();
      await speakQuestion(
        sessionId,
        payload.question.question_text,
        payload.tts_audio_base64,
        payload.tts_mime,
        payload.index,
      );
      setIsAstraSpeaking(false);
    },
    [sessionId],
  );

  const runTurn = useCallback(async () => {
    setPhase('loading');
    const payload = await fetchQuestion();
    if (payload.done) {
      setPhase('done');
      return;
    }
    if (!payload.question) {
      setFatalError('Question payload is missing.');
      setPhase('error');
      return;
    }
    try {
      await playCurrentQuestion(payload);
    } catch (err) {
      setVoiceError(err instanceof Error ? err.message : 'Unable to play question audio.');
    }

    const mic = interviewMedia.current?.micStream;
    if (!mic) {
      setFatalError('Microphone stream unavailable.');
      setPhase('error');
      return;
    }
    setPhase('listening');
    listenAbort.current?.abort();
    const ac = new AbortController();
    listenAbort.current = ac;
    turnActive.current = true;

    try {
      const blob = await listenForAnswer(mic, {
        signal: ac.signal,
        onSilencePrompt: async () => {
          if (!turnActive.current || ac.signal.aborted) return;
          try {
            setIsAstraSpeaking(true);
            await speakAstra(sessionId, SILENCE_NUDGE_SCRIPT);
          } finally {
            setIsAstraSpeaking(false);
          }
        },
        onSkipRequested: () => {
          turnActive.current = false;
        },
      });

      if (!turnActive.current || ac.signal.aborted || !payload.question) return;
      turnActive.current = false;
      setPhase('processing');
      const form = new FormData();
      form.append('question_id', payload.question.id);
      form.append('audio', blob, 'answer.webm');
      await publicApi.post(`/recruitment/ai-sessions/${sessionId}/answers/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await runTurnRef.current();
    } catch (err) {
      if (err instanceof SkipRequestedError && payload.question) {
        setPhase('processing');
        await publicApi.post(`/recruitment/ai-sessions/${sessionId}/questions/skip/`, {
          question_id: payload.question.id,
        });
        await runTurnRef.current();
        return;
      }
      if (err instanceof Error && err.message === 'Listening cancelled') return;
      setFatalError(err instanceof Error ? err.message : 'Could not capture response.');
      setPhase('error');
    }
  }, [fetchQuestion, playCurrentQuestion, sessionId]);

  runTurnRef.current = runTurn;

  const setupMedia = useCallback(async () => {
    setFatalError('');
    setVoiceError('');
    setErrorHidden(false);
    try {
      const token = getInterviewMagicToken(sessionId);
      if (token) {
        try {
          const res = await publicApi.get<SessionMeta>(`/recruitment/ai-sessions/verify/${token}/`);
          setSessionMeta(res.data);
          if (res.data.expires_at) {
            const diff = Math.floor((new Date(res.data.expires_at).getTime() - Date.now()) / 1000);
            setRemainingSeconds(Math.max(0, diff));
          }
        } catch {
          /* continue with fallback timer */
        }
      }
      const media = await acquireInterviewMedia();
      interviewMedia.current = media;
      setPreviewScreen(media.screenStream);
      setPreviewCamera(media.cameraStream);

      const Ctx =
        window.AudioContext ||
        (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (Ctx) {
        const ctx = new Ctx();
        const source = ctx.createMediaStreamSource(media.micStream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        audioContextRef.current = ctx;
        analyserRef.current = analyser;
        dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
      }

      chunkUploader.current = createChunkUploader(sessionId);
      void startInterviewRecording(media, (kind, blob) => chunkUploader.current?.upload(kind, blob))
        .then((recorder) => {
          sessionRecorder.current = recorder;
          setRecorderWarning('');
        })
        .catch(() => {
          setRecorderWarning('Live recording did not start; interview continues.');
        });

      await runTurn();
    } catch (err) {
      setFatalError(err instanceof Error ? err.message : 'Could not initialize interview media.');
      setPhase('setup');
    }
  }, [sessionId, runTurn]);

  const skipCurrentQuestion = useCallback(async () => {
    if (!question?.question) return;
    setPhase('processing');
    await publicApi.post(`/recruitment/ai-sessions/${sessionId}/questions/skip/`, {
      question_id: question.question.id,
    });
    await runTurn();
  }, [question, sessionId, runTurn]);

  const handleSubmitBugReport = useCallback(async () => {
    if (!bugTitle.trim()) {
      setBugMessageType('error');
      setBugMessage('Title is required.');
      return;
    }
    setIsSubmittingBug(true);
    setBugMessage('');
    try {
      const form = new FormData();
      form.append('title', bugTitle.trim());
      form.append('description', bugDescription.trim());
      if (bugImage) form.append('image', bugImage);
      await publicApi.post(`/recruitment/ai-sessions/${sessionId}/bug-report/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setBugMessageType('success');
      setBugMessage('Bug report submitted successfully.');
      setBugTitle('');
      setBugDescription('');
      setBugImage(null);
      window.setTimeout(() => {
        setShowBugModal(false);
        setBugMessage('');
      }, 900);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Could not submit bug report right now.';
      setBugMessageType('error');
      setBugMessage(message);
    } finally {
      setIsSubmittingBug(false);
    }
  }, [bugTitle, bugDescription, bugImage, sessionId]);

  const toggleMic = () => {
    const mic = interviewMedia.current?.micStream;
    if (!mic) return;
    if (isMicMuted) {
      mic.getAudioTracks().forEach((track) => (track.enabled = true));
      setIsMicMuted(false);
    } else {
      mic.getAudioTracks().forEach((track) => (track.enabled = false));
      setIsMicMuted(true);
    }
  };

  const toggleCamera = useCallback(async () => {
    const current = previewCamera;
    if (current) {
      current.getTracks().forEach((track) => track.stop());
      setPreviewCamera(null);
      if (interviewMedia.current) {
        interviewMedia.current.cameraStream = new MediaStream();
      }
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      setPreviewCamera(stream);
      if (interviewMedia.current) {
        interviewMedia.current.cameraStream = stream;
      }
    } catch (err) {
      setVoiceError(err instanceof Error ? err.message : 'Unable to turn on camera.');
    }
  }, [previewCamera]);

  const toggleScreenShare = useCallback(async () => {
    const current = previewScreen;
    if (current) {
      current.getTracks().forEach((track) => track.stop());
      setPreviewScreen(null);
      if (interviewMedia.current) {
        interviewMedia.current.screenStream = new MediaStream();
      }
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.onended = () => {
          setPreviewScreen(null);
          if (interviewMedia.current) interviewMedia.current.screenStream = new MediaStream();
        };
      }
      setPreviewScreen(stream);
      if (interviewMedia.current) {
        interviewMedia.current.screenStream = stream;
      }
    } catch (err) {
      setVoiceError(err instanceof Error ? err.message : 'Unable to start screen share.');
    }
  }, [previewScreen]);

  useEffect(() => {
    return () => {
      listenAbort.current?.abort();
      releaseInterviewMedia(interviewMedia.current);
      if (audioContextRef.current) void audioContextRef.current.close();
    };
  }, []);

  useEffect(() => {
    const canvas = siriCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let width = (canvas.width = canvas.parentElement?.clientWidth || 600);
    let height = (canvas.height = 120);
    const handleResize = () => {
      width = canvas.width = canvas.parentElement?.clientWidth || 600;
      height = canvas.height = 120;
    };
    window.addEventListener('resize', handleResize);
    const colors = [
      'rgba(147, 51, 234, 0.7)',
      'rgba(59, 130, 246, 0.6)',
      'rgba(236, 72, 153, 0.5)',
      'rgba(168, 85, 247, 0.4)',
      'rgba(6, 182, 212, 0.3)',
    ];
    let phaseStep = 0;
    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      let amp = 0.15;
      if (analyserRef.current && dataArrayRef.current && !isMicMuted) {
        const freqData = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(freqData);
        dataArrayRef.current = freqData;
        let sum = 0;
        for (let i = 0; i < dataArrayRef.current.length; i++) sum += dataArrayRef.current[i];
        const avg = sum / dataArrayRef.current.length;
        amp = Math.max(0.1, (avg / 255) * 1.5);
      } else if (isAstraSpeaking) {
        amp = 0.4 + Math.sin(Date.now() / 200) * 0.15;
      } else if (phase === 'listening') {
        amp = 0.2 + Math.sin(Date.now() / 400) * 0.08;
      }
      setAudioLevel(amp);
      ctx.globalCompositeOperation = 'screen';
      for (let i = 0; i < 5; i++) {
        ctx.beginPath();
        const speed = 0.08 + i * 0.015;
        const freq = 0.015 + i * 0.005;
        const baseHeight = i === 0 ? 30 : 20 - i * 2;
        const waveAmp = baseHeight * amp * 1.8;
        for (let x = 0; x < width; x++) {
          const envelope = Math.sin((x / width) * Math.PI);
          const y = height / 2 + Math.sin(x * freq + phaseStep * speed) * waveAmp * envelope;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = colors[i];
        ctx.lineWidth = i === 0 ? 3 : 1.5;
        ctx.shadowBlur = 12;
        ctx.shadowColor = colors[i];
        ctx.stroke();
      }
      phaseStep += 0.8;
      animationFrameRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isAstraSpeaking, phase, isMicMuted]);

  return (
    <div className="h-screen overflow-hidden bg-[#080710] text-slate-100 flex flex-col font-sans">
      <header className="border-b border-neutral-800 bg-neutral-950/80 backdrop-blur-md sticky top-0 z-40 px-3 py-3 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute -inset-1 rounded-lg bg-gradient-to-r from-purple-600 to-pink-500 opacity-60 blur animate-pulse" />
            <div className="relative bg-[#0d0c18] border border-purple-500/30 text-white font-black text-sm tracking-widest px-3 py-1.5 rounded-md flex items-center gap-1.5 shadow-xl">
              <Sparkles className="w-4 h-4 text-pink-400" />
              <span>AASTRAA HR</span>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-xs text-neutral-400 bg-neutral-900 border border-neutral-800 rounded px-2 py-1">
            <span className="font-medium">Questions:</span>
            <div className="flex items-center gap-1">
              {Array.from({ length: totalQuestions || 0 }).map((_, idx) => {
                const n = idx + 1;
                const isActive = n === activeQuestionIndex;
                return (
                  <span
                    key={n}
                    className={`inline-flex h-5 w-5 items-center justify-center rounded-full border text-[10px] ${
                      isActive
                        ? 'bg-gradient-to-r from-orange-500 to-pink-600 border-transparent text-white'
                        : 'bg-neutral-800 border-neutral-700 text-neutral-400'
                    }`}
                  >
                    {n}
                  </span>
                );
              })}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 bg-neutral-900/90 border border-neutral-800/80 rounded-full p-1 text-xs font-semibold">
          <button className="px-3.5 py-1.5 rounded-full text-neutral-400 uppercase">RESUME</button>
          <button className="px-3.5 py-1.5 rounded-full text-neutral-400 uppercase">MEET ASTRA</button>
          <button className="px-3.5 py-1.5 rounded-full text-neutral-400 uppercase">PRE-FLIGHT</button>
          <button className="px-4 py-1.5 rounded-full bg-gradient-to-r from-orange-500 to-pink-600 text-white flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-white rounded-full animate-ping mr-1" />
            INTERVIEW
          </button>
          <button className="px-3.5 py-1.5 rounded-full text-neutral-500 uppercase">COMPLETE</button>
        </div>

        <div
          className={`flex items-center gap-2 text-xs font-mono font-medium rounded-full px-3.5 py-1.5 border ${
            remainingSeconds <= 10
              ? 'text-red-300 bg-red-950/50 border-red-700 animate-pulse'
              : 'text-purple-400 bg-purple-950/40 border-purple-900/50'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>SESSION: {formatCountdown(remainingSeconds)}</span>
        </div>
      </header>

      <main className="flex-1 min-h-0 w-full px-2 md:px-3 py-2 grid grid-cols-1 lg:grid-cols-12 gap-2 items-stretch overflow-hidden">
        <div className="lg:col-span-8 min-h-0 flex flex-col gap-4 overflow-hidden">
          <div className="bg-neutral-950/60 border border-neutral-800 rounded-2xl p-4 relative overflow-hidden">
            <div className="flex items-center justify-between border-b border-neutral-800/80 pb-4 mb-5">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${isAstraSpeaking ? 'bg-pink-500 animate-ping' : 'bg-purple-500 animate-pulse'}`} />
                <span className="text-xs uppercase tracking-wider font-extrabold text-neutral-400">
                  {statusText(phase, isAstraSpeaking)}
                </span>
              </div>
              <div className="text-xs font-bold text-neutral-500 bg-neutral-900 px-2.5 py-1 rounded border border-neutral-800">
                SKIPS: {skipCount}
              </div>
            </div>

            {consolidatedError && (
              <div className="mb-4 rounded-lg border border-red-700 bg-red-950/30 p-3 text-sm text-red-200 flex items-start justify-between gap-3">
                <span>{consolidatedError}</span>
                <button
                  onClick={() => {
                    setErrorHidden(true);
                    setFatalError('');
                    setVoiceError('');
                  }}
                  className="rounded p-1 text-red-200/80 hover:text-red-100 hover:bg-red-900/40"
                  aria-label="Dismiss error"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}

            {!hasRequiredMedia ? (
              <div className="mb-3 flex items-center gap-3 rounded-xl border border-amber-800/60 bg-amber-950/20 px-4 py-3">
                <AlertTriangle className="h-4 w-4 text-amber-300" />
                <div className="text-sm text-amber-200">
                  TURN ON CAMERA AND SCREEN SHARE TO CONTINUE THE INTERVIEW.
                </div>
              </div>
            ) : phase === 'loading' && !question?.question?.question_text ? (
              <div className="mb-3 flex items-center gap-3 rounded-xl border border-purple-800/50 bg-purple-950/20 px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin text-purple-300" />
                <div className="text-sm text-purple-200">
                  AI is preparing the next question...
                </div>
              </div>
            ) : (
              <h2 className="text-xl font-bold text-white mb-3">
                {question?.question?.question_text || (phase === 'setup' ? 'ALLOW PERMISSIONS TO START INTERVIEW' : 'LOADING NEXT QUESTION...')}
              </h2>
            )}

            {sessionMeta.include_assessment && (
              <div className="mb-4 text-xs text-amber-200 bg-amber-950/20 border border-amber-800 rounded-lg px-3 py-2">
                ASSESSMENT IS ENABLED BY HR AND WILL BE SHOWN AFTER VOICE QUESTIONS.
              </div>
            )}

            <div className="mt-6 flex gap-2 items-center">
              {phase === 'setup' || !hasRequiredMedia ? (
                <button onClick={() => void setupMedia()} className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl text-xs font-bold">
                  ALLOW SCREEN + CAMERA + MIC
                </button>
              ) : (
                <button
                  onClick={() => void skipCurrentQuestion()}
                  disabled={!question?.question || phase === 'processing'}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#1a122e] border border-purple-800/60 text-purple-300 rounded-xl text-xs font-bold disabled:opacity-50"
                >
                  <SkipForward className="w-3.5 h-3.5" />
                  SKIP QUESTION
                </button>
              )}
              {recorderWarning && <span className="text-xs text-yellow-300">{recorderWarning}</span>}
            </div>
          </div>

          <div className="bg-neutral-950/60 border border-neutral-800/80 rounded-2xl p-4 relative overflow-hidden">
            <div className="flex items-center justify-between border-b border-neutral-900 pb-3 mb-4">
              <div className="flex items-center gap-3">
                <div className="bg-neutral-900 p-2 rounded-xl border border-neutral-800">
                  <Mic className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    AI LISTENING
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${isMicMuted ? 'text-red-400 bg-red-950/30 border-red-900/30' : 'text-emerald-400 bg-emerald-950/30 border-emerald-900/30'}`}>
                      {isMicMuted ? 'MUTED' : 'ACTIVE'}
                    </span>
                  </h3>
                </div>
              </div>
            </div>
            <div className="relative bg-neutral-950 rounded-xl overflow-hidden border border-neutral-900 p-2 min-h-[140px]">
              <canvas ref={siriCanvasRef} className="w-full h-24 relative z-10 block" />
              <div className="absolute bottom-2 text-[10px] font-semibold text-neutral-500 z-20 flex items-center gap-1.5 left-1/2 -translate-x-1/2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-ping" />
                {isAstraSpeaking ? 'ASTRA SPEAKING' : phase === 'listening' ? 'LISTENING FOR CANDIDATE VOICE...' : 'IDLE'}
              </div>
            </div>
            <div className="mt-2 text-[10px] text-neutral-500 uppercase">MIC LEVEL: {(audioLevel * 100).toFixed(0)}%</div>
          </div>
        </div>

        <div className="lg:col-span-4 min-h-0 flex flex-col gap-2 overflow-hidden lg:h-[calc(100vh-195px)]">
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-neutral-950/80 border border-neutral-800/80 rounded-2xl p-3 flex flex-col items-center justify-center text-center aspect-square">
            <div className="text-[10px] uppercase font-black text-purple-400 bg-purple-950/40 border border-purple-900/50 rounded-full px-3 py-1 mb-4 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 animate-spin" style={{ animationDuration: '4s' }} />
              ASTRA HR RECRUITER NODE
            </div>
            <div className="relative w-40 h-40 flex items-center justify-center my-3">
              <div className={`absolute inset-0 rounded-full border border-purple-500/20 ${isAstraSpeaking ? 'scale-110 animate-ping opacity-60' : 'scale-95 opacity-25'}`} />
              <div className={`absolute w-28 h-28 rounded-full bg-gradient-to-tr from-purple-600 via-pink-600 to-amber-500 blur-[2px] ${isAstraSpeaking ? 'scale-105 rotate-12' : 'scale-95 opacity-90'}`} />
              <div className="relative w-24 h-24 rounded-full bg-neutral-950 border border-white/10 flex flex-col items-center justify-center shadow-inner">
                <span className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-pink-200 bg-clip-text text-transparent">AI</span>
                <span className="text-[9px] uppercase font-extrabold tracking-widest text-pink-400 mt-1">ASTRA</span>
              </div>
            </div>
            <button
              onClick={() => question?.question?.question_text && hasRequiredMedia && void speakAstra(sessionId, question.question.question_text)}
              disabled={!hasRequiredMedia}
              className="mt-3 flex items-center gap-2 text-xs px-3 py-2 bg-neutral-900 border border-neutral-800 rounded-lg text-neutral-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Volume2 className="w-3.5 h-3.5" />
              REPLAY VOICE
            </button>
            </div>

            <div className="bg-neutral-950/80 border border-neutral-800/80 rounded-2xl p-2 flex flex-col min-h-0 aspect-square">
              <div className="flex items-center gap-2 border-b border-neutral-900 pb-2 mb-2">
                <Video className="w-4 h-4 text-pink-400" />
                <span className="text-[10px] font-bold text-white">CANDIDATE CAMERA FEED</span>
              </div>
              <div className="relative bg-neutral-950 rounded-xl border border-neutral-900 overflow-hidden flex-1 flex items-center justify-center">
                {previewCamera ? (
                  <MediaStreamPreview stream={previewCamera} className="w-full h-full object-contain transform -scale-x-100 bg-black" />
                ) : (
                  <div className="text-center p-4">
                    <p className="text-xs text-white font-bold mb-2">CAMERA PREVIEW UNAVAILABLE</p>
                    <button
                      onClick={() => void toggleCamera()}
                      className="text-[11px] px-3 py-1.5 rounded-md border border-purple-700/60 text-purple-300 bg-purple-950/20"
                    >
                      TURN ON CAMERA
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-neutral-950/80 border border-neutral-800/80 rounded-2xl p-2 flex flex-col min-h-0 flex-1">
            <div className="flex items-center gap-2 border-b border-neutral-900 pb-3 mb-3">
              <Monitor className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-white">SCREEN SHARE PREVIEW</span>
            </div>
            <div className="relative bg-neutral-950 h-64 rounded-xl border border-neutral-900 overflow-hidden">
              {previewScreen ? (
                <MediaStreamPreview stream={previewScreen} className="w-full h-full object-contain bg-black" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-xs text-neutral-500">SCREEN PREVIEW UNAVAILABLE</div>
              )}
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-neutral-800/80 bg-neutral-950/90 backdrop-blur-md px-2 md:px-3 py-2 mt-auto">
        <div className="w-full flex flex-col md:flex-row gap-3 items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-[#1e1329] p-2 rounded-xl border border-purple-500/20">
              <Sparkles className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-neutral-400 font-bold tracking-wider">ASTRA INTERACTIVE WORKSPACE</p>
              <p className="text-[10px] text-neutral-500">PROCTORED SESSION ACTIVE.</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={toggleMic} className={`p-3 rounded-full border ${isMicMuted ? 'bg-red-950/40 border-red-900/50 text-red-400' : 'bg-neutral-900 border-neutral-800 text-neutral-300'}`}>
              {isMicMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button
              onClick={() => void toggleCamera()}
              className={`p-3 rounded-full border ${!previewCamera ? 'bg-red-950/40 border-red-900/50 text-red-400' : 'bg-neutral-900 border-neutral-800 text-neutral-300'}`}
            >
              {previewCamera ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
            </button>
            <button
              onClick={() => void toggleScreenShare()}
              className={`p-3 rounded-full border ${!previewScreen ? 'bg-red-950/40 border-red-900/50 text-red-400' : 'bg-neutral-900 border-neutral-800 text-neutral-300'}`}
            >
              <Monitor className="w-4 h-4" />
            </button>
            <button onClick={() => setShowEndModal(true)} className="px-5 py-2.5 bg-rose-600 text-white font-extrabold text-xs rounded-xl flex items-center gap-1.5">
              <PhoneOff className="w-3.5 h-3.5" />
              <span>END INTERVIEW</span>
            </button>
            <button
              onClick={() => {
                setBugMessage('');
                setShowBugModal(true);
              }}
              className="px-4 py-2.5 bg-neutral-900 border border-neutral-700 text-neutral-200 font-semibold text-xs rounded-xl flex items-center gap-1.5"
            >
              <Bug className="w-3.5 h-3.5" />
              <span>REPORT A BUG</span>
            </button>
          </div>
        </div>
      </footer>

      {showEndModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-2xl border border-neutral-700 bg-[#151021] p-5 shadow-2xl">
            <div className="flex items-center gap-2 text-amber-300 mb-3">
              <AlertTriangle className="w-5 h-5" />
              <h3 className="font-bold uppercase">End Interview Session?</h3>
            </div>
            <p className="text-sm text-neutral-300">Your progress will be saved and the session will be finalized.</p>
            <div className="mt-5 flex justify-end gap-2">
              <button onClick={() => setShowEndModal(false)} disabled={isEnding} className="px-4 py-2 rounded-lg border border-neutral-600 text-neutral-300 text-sm">
                Cancel
              </button>
              <button onClick={() => void finishInterview('manual_end')} disabled={isEnding} className="px-4 py-2 rounded-lg bg-rose-600 text-white text-sm font-bold">
                {isEnding ? 'Ending...' : 'End Interview'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showBugModal && (
        <div className="fixed inset-0 z-[55] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl border border-neutral-700 bg-[#151021] p-5 shadow-2xl">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-purple-200">
                <Bug className="w-5 h-5" />
                <h3 className="font-bold uppercase">Report a Bug</h3>
              </div>
              <button
                onClick={() => setShowBugModal(false)}
                disabled={isSubmittingBug}
                className="rounded p-1 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
                aria-label="Close bug report modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-neutral-300 mb-1">Title</label>
                <input
                  value={bugTitle}
                  onChange={(e) => setBugTitle(e.target.value)}
                  placeholder="Short bug title"
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-purple-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-neutral-300 mb-1">Description</label>
                <textarea
                  value={bugDescription}
                  onChange={(e) => setBugDescription(e.target.value)}
                  rows={4}
                  placeholder="What happened? Steps to reproduce..."
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-purple-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-neutral-300 mb-1">Image</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setBugImage(e.target.files?.[0] ?? null)}
                  className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-xs text-neutral-200"
                />
              </div>
              {bugMessage && (
                <div
                  className={`rounded-lg px-3 py-2 text-xs ${
                    bugMessageType === 'success'
                      ? 'border border-emerald-800 bg-emerald-950/30 text-emerald-300'
                      : 'border border-red-800 bg-red-950/30 text-red-300'
                  }`}
                >
                  {bugMessage}
                </div>
              )}
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => setShowBugModal(false)}
                disabled={isSubmittingBug}
                className="px-4 py-2 rounded-lg border border-neutral-600 text-neutral-300 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={() => void handleSubmitBugReport()}
                disabled={isSubmittingBug}
                className="px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-bold disabled:opacity-70"
              >
                {isSubmittingBug ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </div>
        </div>
      )}

      {!hasRequiredMedia && (
        <div className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-2xl border border-amber-700/70 bg-[#151021] p-5 shadow-2xl">
            <div className="flex items-center gap-2 text-amber-300 mb-3">
              <AlertTriangle className="w-5 h-5" />
              <h3 className="font-bold uppercase">Camera + Screen Share Required</h3>
            </div>
            <p className="text-sm text-neutral-200">
              Turn on both camera and screen share to continue. Questions stay hidden until both are active.
            </p>
            <div className="mt-5 flex justify-end">
              <button
                onClick={() => void setupMedia()}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-bold"
              >
                ENABLE NOW
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
