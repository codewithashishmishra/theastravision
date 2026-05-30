import { decryptEnvelope, deriveAesKey, exportPublicKeySpkiB64, generateEcdhKeyPair, isE2EEEnvelope } from './crypto';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

let sessionId: string | null = null;
let aesKey: CryptoKey | null = null;
let privateKey: CryptoKey | null = null;
let seq = 0;
let handshakePromise: Promise<void> | null = null;

async function performPublicHandshake(): Promise<void> {
  const keyPair = await generateEcdhKeyPair();
  const clientPub = await exportPublicKeySpkiB64(keyPair.publicKey);
  const res = await fetch(`${API_BASE}/public/e2ee/handshake/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ client_ecdh_public: clientPub, client_type: 'public' }),
  });
  if (!res.ok) throw new Error('E2EE handshake failed');
  const data = await res.json();
  privateKey = keyPair.privateKey;
  sessionId = data.session_id;
  aesKey = await deriveAesKey(keyPair.privateKey, data.server_ecdh_public, data.session_id);
  seq = 0;
}

export function resetPublicE2EESession(): void {
  sessionId = null;
  aesKey = null;
  privateKey = null;
  seq = 0;
  handshakePromise = null;
}

export async function rehandshakePublic(): Promise<void> {
  resetPublicE2EESession();
  await ensurePublicE2EESession();
}

export async function ensurePublicE2EESession(): Promise<void> {
  if (sessionId && aesKey) return;
  if (!handshakePromise) {
    handshakePromise = performPublicHandshake().finally(() => {
      handshakePromise = null;
    });
  }
  await handshakePromise;
}

export function getPublicSessionId(): string | null {
  return sessionId;
}

export function nextPublicSeq(): number {
  seq += 1;
  return seq;
}

export async function decryptPublicResponse(data: unknown): Promise<unknown> {
  if (!isE2EEEnvelope(data)) return data;
  if (!aesKey) throw new Error('Missing public E2EE session key');
  return decryptEnvelope(aesKey, data);
}

/** Decrypt an E2EE envelope if present; otherwise return data unchanged. */
export async function unwrapPublicApiPayload<T = unknown>(data: unknown): Promise<T> {
  if (!isE2EEEnvelope(data)) return data as T;
  return (await decryptPublicResponse(data)) as T;
}

export function isPublicE2EEError(data: unknown): boolean {
  if (typeof data !== 'object' || data === null) return false;
  const code = (data as { code?: string }).code;
  return code === 'E2EE_HANDSHAKE_REQUIRED' || code === 'E2EE_SESSION_EXPIRED';
}
