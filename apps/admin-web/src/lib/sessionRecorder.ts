/**
 * Composite screen + camera PiP recording for interview proctoring.
 */

import type { ChunkKind } from '@/lib/interviewLiveUpload';

export type SessionRecorder = {
  stop: () => Promise<{ sessionBlob: Blob; cameraBlob: Blob | null }>;
};

export type ChunkUploadHandler = (kind: ChunkKind, blob: Blob) => void | Promise<void>;

const CHUNK_TIMESLICE_MS = 750;
const VIDEO_READY_TIMEOUT_MS = 15_000;

const RECORDER_MIME_CANDIDATES = [
  'video/webm;codecs=vp8,opus',
  'video/webm;codecs=vp9,opus',
  'video/webm',
];

function pickRecorderMimeType(): string | undefined {
  if (typeof MediaRecorder === 'undefined') return undefined;
  for (const mime of RECORDER_MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported(mime)) return mime;
  }
  return undefined;
}

function createPlaybackVideo(): HTMLVideoElement {
  const video = document.createElement('video');
  video.muted = true;
  video.playsInline = true;
  video.setAttribute('playsinline', 'true');
  video.style.position = 'fixed';
  video.style.left = '0';
  video.style.top = '0';
  video.style.width = '1px';
  video.style.height = '1px';
  video.style.opacity = '0';
  video.style.pointerEvents = 'none';
  video.style.zIndex = '-1';
  document.body.appendChild(video);
  return video;
}

/** Wait for stream metadata + play(); hidden videos often hang on play() alone. */
export function waitForVideoReady(
  video: HTMLVideoElement,
  label: string,
  timeoutMs = VIDEO_READY_TIMEOUT_MS,
): Promise<void> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (err?: Error) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      video.removeEventListener('loadedmetadata', onReady);
      video.removeEventListener('playing', onReady);
      if (err) reject(err);
      else resolve();
    };

    const onReady = () => {
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        finish();
      }
    };

    const timer = window.setTimeout(() => {
      finish(new Error(`${label} video failed to start. Try choosing your screen again.`));
    }, timeoutMs);

    video.addEventListener('loadedmetadata', onReady);
    video.addEventListener('playing', onReady);

    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA && video.videoWidth > 0) {
      finish();
      return;
    }

    void video.play().catch((err) => {
      finish(err instanceof Error ? err : new Error(`${label} video play() failed.`));
    });
  });
}

export async function startSessionRecorder(
  screenStream: MediaStream,
  cameraStream: MediaStream | null,
  onChunk?: ChunkUploadHandler,
): Promise<SessionRecorder> {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    throw new Error('Could not start screen recording (canvas unavailable).');
  }

  const screenVideo = createPlaybackVideo();
  screenVideo.srcObject = screenStream;
  try {
    await waitForVideoReady(screenVideo, 'Screen');

    let cameraVideo: HTMLVideoElement | null = null;
    if (cameraStream) {
      cameraVideo = createPlaybackVideo();
      cameraVideo.srcObject = cameraStream;
      await waitForVideoReady(cameraVideo, 'Camera');
    }

    const draw = () => {
      canvas.width = screenVideo.videoWidth || 1280;
      canvas.height = screenVideo.videoHeight || 720;
      ctx.drawImage(screenVideo, 0, 0, canvas.width, canvas.height);
      if (cameraVideo && cameraVideo.videoWidth) {
        const pipW = Math.round(canvas.width * 0.22);
        const pipH = Math.round((pipW / cameraVideo.videoWidth) * cameraVideo.videoHeight);
        ctx.strokeStyle = '#ea580c';
        ctx.lineWidth = 3;
        ctx.drawImage(cameraVideo, canvas.width - pipW - 16, 16, pipW, pipH);
        ctx.strokeRect(canvas.width - pipW - 16, 16, pipW, pipH);
      }
    };

    const interval = window.setInterval(draw, 1000 / 15);
    draw();

    const compositeStream = canvas.captureStream(15);
    const audioTracks = screenStream.getAudioTracks();
    if (audioTracks.length) {
      compositeStream.addTrack(audioTracks[0]);
    }

    const sessionMime = pickRecorderMimeType();
    const sessionRecorder = sessionMime
      ? new MediaRecorder(compositeStream, { mimeType: sessionMime })
      : new MediaRecorder(compositeStream);
    const sessionChunks: Blob[] = [];
    sessionRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        sessionChunks.push(e.data);
        void onChunk?.('session_composite', e.data);
      }
    };
    sessionRecorder.start(CHUNK_TIMESLICE_MS);

    let cameraRecorder: MediaRecorder | null = null;
    const cameraChunks: Blob[] = [];
    const cameraMime = pickRecorderMimeType();
    if (cameraStream) {
      cameraRecorder = cameraMime
        ? new MediaRecorder(cameraStream, { mimeType: cameraMime })
        : new MediaRecorder(cameraStream);
      cameraRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          cameraChunks.push(e.data);
          void onChunk?.('camera', e.data);
        }
      };
      cameraRecorder.start(CHUNK_TIMESLICE_MS);
    }

    const detachVideos = () => {
      window.clearInterval(interval);
      for (const el of [screenVideo, cameraVideo]) {
        if (!el) continue;
        el.pause();
        el.srcObject = null;
        el.remove();
      }
    };

    return {
      stop: () =>
        new Promise((resolve) => {
          let done = false;
          const finish = () => {
            if (done) return;
            done = true;
            detachVideos();
            const sessionBlob = new Blob(sessionChunks, { type: sessionMime || 'video/webm' });
            const cameraBlob = cameraChunks.length
              ? new Blob(cameraChunks, { type: cameraMime || 'video/webm' })
              : null;
            screenStream.getTracks().forEach((t) => t.stop());
            cameraStream?.getTracks().forEach((t) => t.stop());
            resolve({ sessionBlob, cameraBlob });
          };
          const expected = cameraRecorder ? 2 : 1;
          let stopped = 0;
          const onStop = () => {
            stopped += 1;
            if (stopped >= expected) finish();
          };
          sessionRecorder.onstop = onStop;
          if (cameraRecorder) {
            cameraRecorder.onstop = onStop;
            cameraRecorder.stop();
          }
          sessionRecorder.stop();
        }),
    };
  } catch (err) {
    screenVideo.pause();
    screenVideo.srcObject = null;
    screenVideo.remove();
    throw err;
  }
}
