'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type TranscriptLine = {
  sender: 'AI' | 'Candidate';
  text: string;
  time: string;
  question_order?: number | null;
};

export type LiveSocketMessage =
  | { type: 'connected'; role: string; session_id: string }
  | { type: 'transcript_segment'; speaker: string; text: string; ts: string; question_order?: number }
  | { type: 'chunk_available'; kind: string; sequence: number; byte_size: number; created_at: string }
  | { type: 'session_state'; status: string; current_question_index: number; phase: string }
  | { type: 'session_ended'; status: string; ts: string }
  | { type: 'concern_flagged'; note: string; ts: string };

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function wsBaseUrl() {
  return process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000';
}

export function useInterviewLiveSocket(
  sessionId: string | undefined,
  token: string | null,
  role: 'hr' | 'candidate' = 'hr',
) {
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [connected, setConnected] = useState(false);
  const [lastChunk, setLastChunk] = useState<{
    kind: string;
    sequence: number;
    created_at: string;
  } | null>(null);
  const [sessionEnded, setSessionEnded] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const appendTranscript = useCallback((speaker: string, text: string, ts: string) => {
    const sender = speaker === 'AI' ? 'AI' : 'Candidate';
    setTranscript((prev) => [
      ...prev,
      { sender, text, time: formatTime(ts) },
    ]);
  }, []);

  useEffect(() => {
    if (!sessionId || !token) return;

    const param = role === 'hr' ? `token=${encodeURIComponent(token)}` : `magic_token=${encodeURIComponent(token)}`;
    const url = `${wsBaseUrl()}/ws/interviews/${sessionId}/?${param}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as LiveSocketMessage;
        if (msg.type === 'transcript_segment') {
          appendTranscript(msg.speaker, msg.text, msg.ts);
        } else if (msg.type === 'chunk_available') {
          setLastChunk({
            kind: msg.kind,
            sequence: msg.sequence,
            created_at: msg.created_at,
          });
        } else if (msg.type === 'session_ended') {
          setSessionEnded(true);
        }
      } catch {
        /* ignore */
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [sessionId, token, role, appendTranscript]);

  return { transcript, connected, lastChunk, sessionEnded, setTranscript };
}
