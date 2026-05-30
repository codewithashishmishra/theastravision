/**
 * Chunked live upload for interview screen/camera streams.
 */

import publicApi from '@/lib/publicApi';

export type ChunkKind = 'session_composite' | 'camera';

export function getInterviewMagicToken(sessionId: string): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(`interview_magic_${sessionId}`);
}

export function setInterviewMagicToken(sessionId: string, token: string) {
  sessionStorage.setItem(`interview_magic_${sessionId}`, token);
}

const MAX_RETRIES = 3;

async function postChunk(
  sessionId: string,
  magicToken: string,
  kind: ChunkKind,
  sequence: number,
  blob: Blob,
): Promise<void> {
  const form = new FormData();
  form.append('kind', kind);
  form.append('sequence', String(sequence));
  form.append('chunk', blob, `${kind}_${sequence}.webm`);
  form.append('magic_token', magicToken);
  await publicApi.post(`/recruitment/ai-sessions/${sessionId}/live/chunks/`, form, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Interview-Token': magicToken,
    },
  });
}

export function createChunkUploader(sessionId: string) {
  const magicToken = getInterviewMagicToken(sessionId);
  const seq: Record<ChunkKind, number> = {
    session_composite: 0,
    camera: 0,
  };

  return {
    async upload(kind: ChunkKind, blob: Blob) {
      if (!magicToken || blob.size === 0) return;
      const sequence = seq[kind]++;
      let lastErr: unknown;
      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        try {
          await postChunk(sessionId, magicToken, kind, sequence, blob);
          return;
        } catch (err) {
          lastErr = err;
          await new Promise((r) => setTimeout(r, 400 * (attempt + 1)));
        }
      }
      console.warn('Chunk upload failed', kind, sequence, lastErr);
    },
    async finalize(tabSwitchCount: number) {
      if (!magicToken) return;
      await publicApi.post(
        `/recruitment/ai-sessions/${sessionId}/live/finalize-recording/`,
        { tab_switch_count: tabSwitchCount, magic_token: magicToken },
        { headers: { 'X-Interview-Token': magicToken } },
      );
    },
  };
}
