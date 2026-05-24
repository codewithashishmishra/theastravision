import { decryptEnvelope, deriveAesKey, exportPublicKeySpkiB64, isE2EEEnvelope } from './crypto';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

let browserSingleton: E2EEClient | null = null;

export class E2EEClient {
  private sessionId: string | null = null;
  private aesKey: CryptoKey | null = null;
  private privateKey: CryptoKey | null = null;
  private seq = 0;

  async ensureSession(): Promise<void> {
    if (this.sessionId && this.aesKey) return;
    const keyPair = await crypto.subtle.generateKey(
      { name: 'ECDH', namedCurve: 'P-256' },
      true,
      ['deriveBits']
    );
    const clientPub = await exportPublicKeySpkiB64(keyPair.publicKey);
    const res = await fetch(`${API_BASE}/public/e2ee/handshake/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ client_ecdh_public: clientPub, client_type: 'public' }),
    });
    if (!res.ok) throw new Error('E2EE handshake failed');
    const data = await res.json();
    this.privateKey = keyPair.privateKey;
    this.sessionId = data.session_id;
    this.aesKey = await deriveAesKey(keyPair.privateKey, data.server_ecdh_public, data.session_id);
    this.seq = 0;
  }

  private nextSeq(): number {
    this.seq += 1;
    return this.seq;
  }

  async getRequestHeaders(extra?: HeadersInit): Promise<Headers> {
    await this.ensureSession();
    const headers = new Headers(extra);
    headers.set('Accept', 'application/json');
    if (this.sessionId) {
      headers.set('X-E2EE-Session', this.sessionId);
      headers.set('X-E2EE-Seq', String(this.nextSeq()));
    }
    return headers;
  }

  async parseResponse<T>(res: Response): Promise<T> {
    const data = await res.json();
    if (isE2EEEnvelope(data) && this.aesKey) {
      return (await decryptEnvelope(this.aesKey, data)) as T;
    }
    return data as T;
  }

  async fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
    const headers = await this.getRequestHeaders(init?.headers);
    const res = await fetch(url, { ...init, headers });
    const data = await this.parseResponse<T>(res);
    if (!res.ok) {
      throw new Error(typeof (data as { detail?: string }).detail === 'string' ? (data as { detail: string }).detail : 'Request failed');
    }
    return data;
  }
}

export function getBrowserE2EEClient(): E2EEClient {
  if (!browserSingleton) browserSingleton = new E2EEClient();
  return browserSingleton;
}

export function createE2EEClient(): E2EEClient {
  return new E2EEClient();
}

export async function e2eeJsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const client =
    typeof window !== 'undefined' ? getBrowserE2EEClient() : createE2EEClient();
  return client.fetchJson<T>(url, init);
}
