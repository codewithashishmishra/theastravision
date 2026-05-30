/**
 * Auto-capture candidate answers with simple VAD and optional skip-phrase detection.
 */

export class SkipRequestedError extends Error {
  constructor() {
    super('Skip requested');
    this.name = 'SkipRequestedError';
  }
}

export const SILENCE_PROMPT_MS = 5000;
export const END_SILENCE_MS = 2000;
export const MAX_ANSWER_MS = 120000;
const SPEECH_RMS_THRESHOLD = 0.018;
const ANALYSE_INTERVAL_MS = 100;

export type ListenForAnswerOptions = {
  silencePromptMs?: number;
  endSilenceMs?: number;
  maxDurationMs?: number;
  onSilencePrompt?: () => void | Promise<void>;
  onSkipRequested?: () => void;
  onAudioLevel?: (rms: number) => void;
  signal?: AbortSignal;
};

function rmsFromAnalyser(analyser: AnalyserNode): number {
  const data = new Uint8Array(analyser.fftSize);
  analyser.getByteTimeDomainData(data);
  let sum = 0;
  for (let i = 0; i < data.length; i++) {
    const v = (data[i] - 128) / 128;
    sum += v * v;
  }
  return Math.sqrt(sum / data.length);
}

function isSkipPhrase(transcript: string): boolean {
  const t = transcript.toLowerCase();
  return /\bskip\b/.test(t) && (/\bquestion\b/.test(t) || /\bthis\b/.test(t) || t.trim() === 'skip');
}

type SpeechRecognitionCtor = new () => {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((ev: { results: { length: number; [i: number]: { [j: number]: { transcript: string } } } }) => void) | null;
  onerror: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

function startSkipPhraseListener(onSkip: () => void, signal?: AbortSignal): (() => void) | null {
  if (typeof window === 'undefined') return null;
  const Win = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  const Ctor = Win.SpeechRecognition || Win.webkitSpeechRecognition;
  if (!Ctor) return null;

  const recognition = new Ctor();
  recognition.lang = 'en-IN';
  recognition.continuous = true;
  recognition.interimResults = true;
  let stopped = false;

  recognition.onresult = (ev) => {
    if (stopped) return;
    let text = '';
    for (let i = 0; i < ev.results.length; i++) {
      text += ev.results[i][0].transcript;
    }
    if (isSkipPhrase(text)) {
      stopped = true;
      recognition.stop();
      onSkip();
    }
  };
  recognition.onerror = () => {
    /* ignore — skip button remains available */
  };

  try {
    recognition.start();
  } catch {
    return null;
  }

  const cleanup = () => {
    if (stopped) return;
    stopped = true;
    try {
      recognition.abort();
    } catch {
      try {
        recognition.stop();
      } catch {
        /* noop */
      }
    }
  };

  signal?.addEventListener('abort', cleanup);
  return cleanup;
}

export function listenForAnswer(
  micStream: MediaStream,
  options: ListenForAnswerOptions = {},
): Promise<Blob> {
  const silencePromptMs = options.silencePromptMs ?? SILENCE_PROMPT_MS;
  const endSilenceMs = options.endSilenceMs ?? END_SILENCE_MS;
  const maxDurationMs = options.maxDurationMs ?? MAX_ANSWER_MS;

  return new Promise((resolve, reject) => {
    const chunks: Blob[] = [];
    const recorder = new MediaRecorder(micStream, { mimeType: 'audio/webm' });
    let disposed = false;

    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(micStream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);

    let speechDetected = false;
    let silencePromptFired = false;
    let lastSpeechAt = Date.now();
    const startedAt = Date.now();
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const dispose = () => {
      if (disposed) return;
      disposed = true;
      if (intervalId) clearInterval(intervalId);
      stopSkipListener?.();
      try {
        source.disconnect();
        void audioContext.close();
      } catch {
        /* noop */
      }
    };

    const finish = (blob: Blob) => {
      dispose();
      resolve(blob);
    };

    const fail = (err: Error) => {
      dispose();
      if (recorder.state !== 'inactive') {
        try {
          recorder.stop();
        } catch {
          /* noop */
        }
      }
      reject(err);
    };

    const stopSkipListener = options.onSkipRequested
      ? startSkipPhraseListener(() => {
          if (disposed) return;
          disposed = true;
          if (intervalId) clearInterval(intervalId);
          if (recorder.state !== 'inactive') {
            try {
              recorder.stop();
            } catch {
              /* noop */
            }
          }
          dispose();
          options.onSkipRequested?.();
          reject(new SkipRequestedError());
        }, options.signal)
      : null;

    options.signal?.addEventListener('abort', () => {
      fail(new Error('Listening cancelled'));
    });

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    recorder.onstop = () => {
      if (options.signal?.aborted) return;
      finish(new Blob(chunks, { type: 'audio/webm' }));
    };

    recorder.onerror = () => fail(new Error('Recording failed'));

    recorder.start(250);

    intervalId = setInterval(() => {
      if (disposed || options.signal?.aborted) return;

      const now = Date.now();
      const rms = rmsFromAnalyser(analyser);
      options.onAudioLevel?.(rms);

      if (rms >= SPEECH_RMS_THRESHOLD) {
        speechDetected = true;
        lastSpeechAt = now;
      }

      if (!speechDetected && !silencePromptFired && now - startedAt >= silencePromptMs) {
        silencePromptFired = true;
        void options.onSilencePrompt?.();
      }

      if (speechDetected && now - lastSpeechAt >= endSilenceMs) {
        if (recorder.state !== 'inactive') recorder.stop();
        return;
      }

      if (now - startedAt >= maxDurationMs) {
        if (recorder.state !== 'inactive') recorder.stop();
      }
    }, ANALYSE_INTERVAL_MS);
  });
}
