'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import api from '@/lib/axios';

/**
 * Append WebM chunks to a video element via Media Source Extensions.
 */
export function useInterviewMsePlayer(sessionId: string | undefined, kind: string) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaSourceRef = useRef<MediaSource | null>(null);
  const sourceBufferRef = useRef<SourceBuffer | null>(null);
  const queueRef = useRef<ArrayBuffer[]>([]);
  const appendedSequences = useRef<Set<number>>(new Set());
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [error, setError] = useState('');

  const flushQueue = useCallback(() => {
    const sb = sourceBufferRef.current;
    if (!sb || sb.updating || queueRef.current.length === 0) return;
    const chunk = queueRef.current.shift();
    if (chunk) {
      try {
        sb.appendBuffer(chunk);
      } catch {
        setError('Playback buffer error');
      }
    }
  }, []);

  const ensureMediaSource = useCallback(() => {
    const video = videoRef.current;
    if (!video || mediaSourceRef.current) return;
    if (typeof MediaSource === 'undefined' || !MediaSource.isTypeSupported('video/webm; codecs=vp8,opus')) {
      setError('Live playback not supported in this browser');
      return;
    }
    const ms = new MediaSource();
    mediaSourceRef.current = ms;
    video.src = URL.createObjectURL(ms);
    ms.addEventListener('sourceopen', () => {
      try {
        const sb = ms.addSourceBuffer('video/webm; codecs=vp8,opus');
        sourceBufferRef.current = sb;
        sb.addEventListener('updateend', flushQueue);
        flushQueue();
      } catch {
        setError('Could not initialize live player');
      }
    });
  }, [flushQueue]);

  const appendChunk = useCallback(
    async (sequence: number, createdAt?: string) => {
      if (!sessionId || appendedSequences.current.has(sequence)) return;
      appendedSequences.current.add(sequence);
      ensureMediaSource();
      try {
        const res = await api.get(
          `/recruitment/ai-sessions/${sessionId}/live/chunks/${kind}/${sequence}/`,
          { responseType: 'arraybuffer' },
        );
        const buf = res.data as ArrayBuffer;
        queueRef.current.push(buf);
        flushQueue();
        if (createdAt) {
          const delay = Date.now() - new Date(createdAt).getTime();
          if (delay >= 0 && delay < 60000) setLatencyMs(delay);
        }
        const video = videoRef.current;
        if (video && video.paused) {
          void video.play().catch(() => {});
        }
      } catch {
        appendedSequences.current.delete(sequence);
      }
    },
    [sessionId, kind, ensureMediaSource, flushQueue],
  );

  const pollChunks = useCallback(
    async (since: number) => {
      if (!sessionId) return since;
      try {
        const res = await api.get<{ chunks: Array<{ kind: string; sequence: number; created_at: string }> }>(
          `/recruitment/ai-sessions/${sessionId}/live/chunks/list/`,
          { params: { kind, since } },
        );
        let maxSeq = since;
        for (const c of res.data.chunks || []) {
          if (c.kind === kind && c.sequence > since) {
            await appendChunk(c.sequence, c.created_at);
            maxSeq = Math.max(maxSeq, c.sequence);
          }
        }
        return maxSeq;
      } catch {
        return since;
      }
    },
    [sessionId, kind, appendChunk],
  );

  useEffect(() => {
    if (!sessionId) return;
    let since = 0;
    const interval = setInterval(() => {
      void pollChunks(since).then((s) => {
        since = s;
      });
    }, 500);
    return () => clearInterval(interval);
  }, [sessionId, pollChunks]);

  useEffect(() => {
    return () => {
      const video = videoRef.current;
      if (video?.src) URL.revokeObjectURL(video.src);
      mediaSourceRef.current = null;
      sourceBufferRef.current = null;
    };
  }, []);

  return { videoRef, appendChunk, latencyMs, error };
}
