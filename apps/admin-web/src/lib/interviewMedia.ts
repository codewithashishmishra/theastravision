/**
 * Screen, camera, and microphone access for live AI interviews.
 */

import { acquireProcessedMicStream, MIC_AUDIO_CONSTRAINTS } from '@/lib/interviewMicProcessing';
import type { ChunkKind } from '@/lib/interviewLiveUpload';
import { startSessionRecorder, type ChunkUploadHandler, type SessionRecorder } from '@/lib/sessionRecorder';

export type InterviewMediaResult = {
  screenStream: MediaStream;
  cameraStream: MediaStream;
  /** Noise-suppressed mic (Web Audio processed). */
  micStream: MediaStream;
  cleanupMic?: () => void;
};

export type MediaSetupStep = 'screen' | 'camera' | 'microphone' | 'done';

export const MEDIA_SETUP_TIMEOUT_MS = 30_000;

export function releaseInterviewMedia(media: InterviewMediaResult | null | undefined): void {
  if (!media) return;
  media.cleanupMic?.();
  for (const stream of [media.screenStream, media.cameraStream, media.micStream]) {
    stream.getTracks().forEach((t) => t.stop());
  }
}

function withTimeout<T>(promise: Promise<T>, ms: number, message: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => reject(new Error(message)), ms);
    promise
      .then((v) => {
        window.clearTimeout(timer);
        resolve(v);
      })
      .catch((err) => {
        window.clearTimeout(timer);
        reject(err);
      });
  });
}

async function requestScreenCapture(): Promise<MediaStream> {
  const constraints: DisplayMediaStreamOptions = {
    video: { displaySurface: 'monitor' } as MediaTrackConstraints,
    audio: true,
  };
  try {
    return await navigator.mediaDevices.getDisplayMedia(constraints);
  } catch {
    return navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
  }
}

/**
 * Acquire screen, camera, and mic only (no recorder). Fast path to start interview + API.
 */
export async function acquireInterviewMedia(
  onStep?: (step: MediaSetupStep) => void,
): Promise<InterviewMediaResult> {
  let screenStream: MediaStream | null = null;
  let cameraStream: MediaStream | null = null;
  let micStream: MediaStream | null = null;
  let cleanupMic: (() => void) | undefined;

  const releasePartial = () => {
    cleanupMic?.();
    cleanupMic = undefined;
    screenStream?.getTracks().forEach((t) => t.stop());
    cameraStream?.getTracks().forEach((t) => t.stop());
    micStream?.getTracks().forEach((t) => t.stop());
  };

  onStep?.('screen');
  try {
    screenStream = await withTimeout(
      requestScreenCapture(),
      MEDIA_SETUP_TIMEOUT_MS,
      'Screen sharing timed out. When prompted, choose your screen or window (check pop-ups if you see no picker).',
    );
  } catch (err) {
    if (err instanceof Error && err.message.includes('timed out')) throw err;
    throw new Error('Screen sharing is required. Allow screen capture when prompted.');
  }

  onStep?.('camera');
  try {
    cameraStream = await withTimeout(
      navigator.mediaDevices.getUserMedia({ video: true, audio: false }),
      MEDIA_SETUP_TIMEOUT_MS,
      'Camera access timed out. Check browser permissions.',
    );
  } catch (err) {
    releasePartial();
    if (err instanceof Error && err.message.includes('timed out')) throw err;
    throw new Error('Camera access is required. Check browser permissions.');
  }

  onStep?.('microphone');
  try {
    const processed = await withTimeout(
      acquireProcessedMicStream(),
      MEDIA_SETUP_TIMEOUT_MS,
      'Microphone access timed out. Check browser permissions.',
    );
    micStream = processed.stream;
    cleanupMic = processed.cleanup;
  } catch (err) {
    releasePartial();
    if (err instanceof Error && err.message.includes('timed out')) throw err;
    throw new Error('Microphone access is required. Check browser permissions.');
  }

  onStep?.('done');
  return { screenStream, cameraStream, micStream, cleanupMic };
}

/** Start composite + camera recorders (optional; must not block interview start). */
export async function startInterviewRecording(
  media: InterviewMediaResult,
  onChunk?: ChunkUploadHandler,
): Promise<SessionRecorder> {
  return startSessionRecorder(media.screenStream, media.cameraStream, onChunk);
}

/** @deprecated Use acquireInterviewMedia + startInterviewRecording */
export async function requestInterviewMedia(): Promise<InterviewMediaResult> {
  return acquireInterviewMedia();
}

/** Probe a device for the media-failed recovery UI (stops tracks immediately). */
export async function probeScreenShare(): Promise<void> {
  const s = await requestScreenCapture();
  s.getTracks().forEach((t) => t.stop());
}

export async function probeCamera(): Promise<void> {
  const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  s.getTracks().forEach((t) => t.stop());
}

export async function probeMicrophone(): Promise<void> {
  const s = await navigator.mediaDevices.getUserMedia({
    audio: MIC_AUDIO_CONSTRAINTS,
    video: false,
  });
  s.getTracks().forEach((t) => t.stop());
}

export type { ChunkKind, SessionRecorder };
