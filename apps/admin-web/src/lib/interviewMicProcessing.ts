/**
 * Microphone capture with browser noise suppression + Web Audio cleanup.
 * Used for conversational interview answers (not raw mic passthrough).
 */

export const MIC_AUDIO_CONSTRAINTS: MediaTrackConstraints = {
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
  channelCount: { ideal: 1 },
};

export type ProcessedMicStream = {
  stream: MediaStream;
  /** Stops raw tracks and closes the processing AudioContext. */
  cleanup: () => void;
};

/**
 * Request microphone with OS/browser noise cancellation enabled.
 */
export async function acquireRawMicStream(): Promise<MediaStream> {
  return navigator.mediaDevices.getUserMedia({
    audio: MIC_AUDIO_CONSTRAINTS,
    video: false,
  });
}

/**
 * Pipe mic audio through high-pass + dynamics compression to reduce background noise.
 */
export function applyMicNoiseProcessing(rawStream: MediaStream): ProcessedMicStream {
  const audioContext = new AudioContext();

  const source = audioContext.createMediaStreamSource(rawStream);

  const highPass = audioContext.createBiquadFilter();
  highPass.type = 'highpass';
  highPass.frequency.value = 100;
  highPass.Q.value = 0.7;

  const compressor = audioContext.createDynamicsCompressor();
  compressor.threshold.value = -24;
  compressor.knee.value = 12;
  compressor.ratio.value = 3;
  compressor.attack.value = 0.003;
  compressor.release.value = 0.15;

  const destination = audioContext.createMediaStreamDestination();

  source.connect(highPass);
  highPass.connect(compressor);
  compressor.connect(destination);

  const cleanup = () => {
    try {
      source.disconnect();
      highPass.disconnect();
      compressor.disconnect();
    } catch {
      /* already disconnected */
    }
    destination.stream.getTracks().forEach((t) => t.stop());
    rawStream.getTracks().forEach((t) => t.stop());
    void audioContext.close();
  };

  return { stream: destination.stream, cleanup };
}

/** Browser constraints + Web Audio noise cleanup in one step. */
export async function acquireProcessedMicStream(): Promise<ProcessedMicStream> {
  const raw = await acquireRawMicStream();
  try {
    return applyMicNoiseProcessing(raw);
  } catch (err) {
    raw.getTracks().forEach((t) => t.stop());
    throw err;
  }
}
