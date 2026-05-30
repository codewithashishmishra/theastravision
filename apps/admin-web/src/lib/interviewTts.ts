/**
 * Astra interviewer voice — self-hosted xyz TTS via /speak/ (JSON + base64).
 * Persists on server as {sessionId}_{n}.mp3; plays automatically in background.
 */

import publicApi from '@/lib/publicApi';

export const TTS_MAX_ATTEMPTS = 3;

export type SpeakResponse = {
  tts_audio_base64?: string | null;
  tts_mime?: string;
  tts_available?: boolean;
  tts_attempts?: number;
  tts_sequence?: number | null;
  tts_filename?: string | null;
  error?: string;
};

const AUDIO_UNLOCK_STORAGE_KEY = 'astra_interview_audio_unlocked';

let interviewAudioCtx: AudioContext | null = null;
let interviewAudioUnlocked = false;
let backgroundAudio: HTMLAudioElement | null = null;
let backgroundObjectUrl: string | null = null;

export function isInterviewAudioUnlocked(): boolean {
  if (interviewAudioUnlocked) return true;
  if (typeof sessionStorage === 'undefined') return false;
  return sessionStorage.getItem(AUDIO_UNLOCK_STORAGE_KEY) === '1';
}

function markInterviewAudioUnlocked(): void {
  interviewAudioUnlocked = true;
  try {
    sessionStorage.setItem(AUDIO_UNLOCK_STORAGE_KEY, '1');
  } catch {
    /* private mode */
  }
}

function getBackgroundAudio(): HTMLAudioElement {
  if (typeof document === 'undefined') {
    throw new Error('Audio playback is only available in the browser.');
  }
  if (!backgroundAudio) {
    backgroundAudio = document.createElement('audio');
    backgroundAudio.id = 'astra-interview-audio';
    backgroundAudio.setAttribute('playsinline', 'true');
    backgroundAudio.setAttribute('preload', 'auto');
    backgroundAudio.volume = 1;
    backgroundAudio.muted = false;
    backgroundAudio.style.display = 'none';
    document.body.appendChild(backgroundAudio);
  }
  return backgroundAudio;
}

function revokeBackgroundUrl() {
  if (backgroundObjectUrl) {
    URL.revokeObjectURL(backgroundObjectUrl);
    backgroundObjectUrl = null;
  }
}

async function getInterviewAudioContext(): Promise<AudioContext> {
  if (typeof window === 'undefined') {
    throw new Error('Audio playback is only available in the browser.');
  }
  if (!interviewAudioCtx) {
    interviewAudioCtx = new AudioContext();
  }
  if (interviewAudioCtx.state === 'suspended') {
    await interviewAudioCtx.resume();
  }
  return interviewAudioCtx;
}

const AUDIO_UNLOCK_MAX_MS = 2000;

function raceTimeout<T>(promise: Promise<T>, ms: number): Promise<T | undefined> {
  return Promise.race([
    promise,
    new Promise<undefined>((resolve) => window.setTimeout(() => resolve(undefined), ms)),
  ]);
}

/**
 * Call inside a click/tap handler. Never blocks long — empty <audio>.play() can hang in Firefox.
 */
export async function unlockInterviewAudio(): Promise<void> {
  if (typeof window === 'undefined') return;

  const unlockWork = async () => {
    const ctx = await raceTimeout(getInterviewAudioContext(), AUDIO_UNLOCK_MAX_MS);
    if (!ctx) return;

    const buffer = ctx.createBuffer(1, 1, ctx.sampleRate);
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);
    await new Promise<void>((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        resolve();
      };
      source.onended = finish;
      try {
        source.start(0);
      } catch {
        finish();
        return;
      }
      window.setTimeout(finish, 80);
    });

    // Do not await play() on an element with no src — Firefox can hang indefinitely.
    const el = getBackgroundAudio();
    el.muted = false;
    void raceTimeout(el.play(), 500).then(() => {
      el.pause();
      el.currentTime = 0;
    });
  };

  try {
    await raceTimeout(unlockWork(), AUDIO_UNLOCK_MAX_MS);
  } catch {
    /* continue */
  }
  markInterviewAudioUnlocked();
}

function normalizeBase64(input: string): string {
  const trimmed = input.trim();
  if (trimmed.startsWith('data:')) {
    const comma = trimmed.indexOf(',');
    return comma >= 0 ? trimmed.slice(comma + 1) : trimmed;
  }
  return trimmed.replace(/\s/g, '');
}

function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(normalizeBase64(base64));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function synthesisUnavailableMessage(data: SpeakResponse): string {
  const attempts = data.tts_attempts;
  if (data.error) return data.error;
  if (data.tts_available === false) {
    return attempts
      ? `Astra voice synthesis failed after ${attempts} attempt(s). Please reload and try again.`
      : 'Astra voice synthesis is unavailable. Please reload and try again.';
  }
  return 'Astra voice is unavailable. Please reload and try again.';
}

function playbackBlockedMessage(): string {
  return 'Browser blocked Astra voice. Tap "Enable Astra voice" on this page, or use Play Astra voice below.';
}

/** Play MP3 bytes (blob from /speak/ base64 or GET …/tts/n/). */
export async function playInterviewAudioBlob(bytes: Uint8Array, mime = 'audio/mpeg'): Promise<void> {
  if (bytes.length < 128) {
    throw new Error('Astra voice audio was empty or too small to play.');
  }

  let lastError: Error | null = null;
  const preferWebAudio = isInterviewAudioUnlocked();

  for (let attempt = 1; attempt <= TTS_MAX_ATTEMPTS; attempt++) {
    if (preferWebAudio || attempt > 1) {
      try {
        await playWithWebAudio(bytes);
        return;
      } catch (waErr) {
        lastError = waErr instanceof Error ? waErr : new Error('Web Audio playback failed.');
      }
    }

    try {
      await playBytesInBackground(bytes, mime);
      return;
    } catch (htmlErr) {
      lastError = htmlErr instanceof Error ? htmlErr : new Error('HTML audio playback failed.');
      if (lastError.message.includes('blocked')) {
        throw lastError;
      }
    }

    if (attempt < TTS_MAX_ATTEMPTS) {
      await sleep(300 * attempt);
    }
  }
  throw lastError ?? new Error('Could not play Astra voice audio.');
}

/** Cache utterance blob in sessionStorage for debugging (named {sessionId}_{n}.mp3). */
function cacheUtteranceBlob(sessionId: string, sequence: number | undefined, bytes: Uint8Array, mime: string) {
  if (typeof sessionStorage === 'undefined' || sequence == null) return;
  try {
    const blob = new Blob([bytes.slice()], { type: mime });
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        sessionStorage.setItem(
          `astra_tts_${sessionId}_${sequence}`,
          JSON.stringify({ mime, dataUrl: reader.result, filename: `${sessionId}_${sequence}.mp3` }),
        );
      }
    };
    reader.readAsDataURL(blob);
  } catch {
    /* optional cache */
  }
}

/**
 * Play MP3 in a persistent hidden <audio> element (background autoplay).
 */
function playBytesInBackground(bytes: Uint8Array, mime: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const audio = getBackgroundAudio();
    revokeBackgroundUrl();
    const blob = new Blob([bytes.slice()], { type: mime || 'audio/mpeg' });
    backgroundObjectUrl = URL.createObjectURL(blob);
    audio.src = backgroundObjectUrl;
    audio.volume = 1;
    audio.muted = false;
    audio.currentTime = 0;

    const cleanup = () => {
      audio.onended = null;
      audio.onerror = null;
    };

    audio.onended = () => {
      cleanup();
      resolve();
    };
    audio.onerror = () => {
      cleanup();
      revokeBackgroundUrl();
      reject(new Error('Audio element could not play Astra voice.'));
    };

    const start = () => {
      void audio.play().catch((err) => {
        cleanup();
        revokeBackgroundUrl();
        if (err instanceof DOMException && err.name === 'NotAllowedError') {
          reject(new Error(playbackBlockedMessage()));
          return;
        }
        reject(err instanceof Error ? err : new Error('Audio play() was rejected.'));
      });
    };

    if (audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) {
      start();
    } else {
      audio.addEventListener('canplaythrough', start, { once: true });
      audio.load();
    }
  });
}

async function playWithWebAudio(bytes: Uint8Array): Promise<void> {
  const ctx = await getInterviewAudioContext();
  const ab = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
  const audioBuffer = await ctx.decodeAudioData(ab);
  await new Promise<void>((resolve, reject) => {
    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(ctx.destination);
    source.onended = () => resolve();
    try {
      source.start(0);
    } catch (err) {
      reject(err);
    }
  });
}

async function playBase64Audio(serverBase64: string, serverMime?: string): Promise<void> {
  const bytes = base64ToUint8Array(serverBase64);
  await playInterviewAudioBlob(bytes, serverMime || 'audio/mpeg');
}

/** Stream persisted clip GET …/tts/{n}/ and autoplay ({sessionId}_{n}.mp3). */
export async function playTtsSequence(sessionId: string, sequence: number): Promise<void> {
  const res = await publicApi.get<ArrayBuffer>(
    `/recruitment/ai-sessions/${sessionId}/tts/${sequence}/`,
    { responseType: 'arraybuffer' },
  );
  const bytes = new Uint8Array(res.data);
  cacheUtteranceBlob(sessionId, sequence, bytes, 'audio/mpeg');
  await playInterviewAudioBlob(bytes, 'audio/mpeg');
}

/** Play base64 from /speak/ immediately (autoplay in background). */
export async function playSpeakResponse(
  data: SpeakResponse,
  sessionId?: string,
): Promise<void> {
  if (!data.tts_audio_base64) {
    throw new Error(synthesisUnavailableMessage(data));
  }
  const bytes = base64ToUint8Array(data.tts_audio_base64);
  if (sessionId && data.tts_sequence != null) {
    cacheUtteranceBlob(sessionId, data.tts_sequence, bytes, data.tts_mime || 'audio/mpeg');
  }
  await playBase64Audio(data.tts_audio_base64, data.tts_mime);
}

/** Fetch TTS from /speak/ with retries. */
export async function fetchAstraSpeech(
  sessionId: string,
  text: string,
  options?: { utteranceIndex?: number },
): Promise<SpeakResponse> {
  let lastError: Error | null = null;
  for (let attempt = 1; attempt <= TTS_MAX_ATTEMPTS; attempt++) {
    try {
      const res = await publicApi.post<SpeakResponse>(
        `/recruitment/ai-sessions/${sessionId}/speak/`,
        {
          text,
          utterance_index: options?.utteranceIndex,
        },
      );
      const data = res.data;
      if (!data.tts_audio_base64) {
        throw new Error(synthesisUnavailableMessage(data));
      }
      return data;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error('Failed to load Astra voice.');
      if (attempt < TTS_MAX_ATTEMPTS) {
        await sleep(400 * attempt);
      }
    }
  }
  throw lastError ?? new Error('Failed to load Astra voice.');
}

/** Fetch /speak/, persist clip as {sessionId}_{n}.mp3 on server, autoplay in background. */
export async function speakAstra(
  sessionId: string,
  text: string,
  options?: { utteranceIndex?: number },
): Promise<SpeakResponse> {
  let lastError: Error | null = null;
  for (let attempt = 1; attempt <= TTS_MAX_ATTEMPTS; attempt++) {
    try {
      const data = await fetchAstraSpeech(sessionId, text, options);
      await playSpeakResponse(data, sessionId);
      return data;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error('Failed to load Astra voice.');
      if (attempt < TTS_MAX_ATTEMPTS) {
        await sleep(400 * attempt);
      }
    }
  }
  throw lastError ?? new Error('Failed to load Astra voice.');
}

/**
 * Question audio: play persisted {sessionId}_{order}.mp3 when available, else /speak/.
 */
export async function speakQuestion(
  sessionId: string,
  questionText: string,
  _serverBase64?: string | null,
  _serverMime?: string,
  questionOrder?: number,
): Promise<void> {
  if (questionOrder != null) {
    try {
      await playTtsSequence(sessionId, questionOrder);
      return;
    } catch {
      /* blob missing — synthesize via /speak/ */
    }
  }
  await speakAstra(sessionId, questionText, { utteranceIndex: questionOrder });
}

export async function playQuestionAudio(
  sessionId: string,
  questionText: string,
  serverBase64?: string | null,
  serverMime?: string,
  questionOrder?: number,
): Promise<void> {
  await speakQuestion(sessionId, questionText, serverBase64, serverMime, questionOrder);
}

export function stopBackgroundInterviewAudio() {
  if (backgroundAudio) {
    backgroundAudio.pause();
    backgroundAudio.currentTime = 0;
  }
  revokeBackgroundUrl();
}
