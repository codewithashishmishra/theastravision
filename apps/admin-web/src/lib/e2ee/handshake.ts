import {
  deriveAesKey,
  exportPublicKeySpkiB64,
  generateEcdhKeyPair,
} from './crypto';
import {
  clearE2EESession,
  getPrivateKey,
  getServerPublicB64,
  hasE2EESession,
  setE2EESession,
} from './sessionStore';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

let handshakePromise: Promise<void> | null = null;
let keyPair: CryptoKeyPair | null = null;

export async function getClientEcdhPublicB64(): Promise<string | null> {
  if (!keyPair) {
    await ensureE2EESession();
  }
  if (!keyPair) return null;
  return exportPublicKeySpkiB64(keyPair.publicKey);
}

export async function ensureE2EESession(): Promise<void> {
  if (hasE2EESession()) return;
  if (!handshakePromise) {
    handshakePromise = performHandshake().finally(() => {
      handshakePromise = null;
    });
  }
  await handshakePromise;
}

async function performHandshake(): Promise<void> {
  keyPair = await generateEcdhKeyPair();
  const clientPub = await exportPublicKeySpkiB64(keyPair.publicKey);
  const res = await fetch(`${API_BASE}/public/e2ee/handshake/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ client_ecdh_public: clientPub, client_type: 'web' }),
  });
  if (!res.ok) {
    throw new Error('E2EE handshake failed');
  }
  const data = await res.json();
  const aesKey = await deriveAesKey(keyPair.privateKey, data.server_ecdh_public, data.session_id);
  setE2EESession(data.session_id, aesKey, keyPair.privateKey, data.server_ecdh_public);
}

export async function establishSessionFromLoginResponse(data: {
  e2ee_session_id?: string;
  server_ecdh_public?: string;
}): Promise<void> {
  if (!data.server_ecdh_public || !data.e2ee_session_id) return;
  const priv = getPrivateKey();
  if (!priv) return;
  const aesKey = await deriveAesKey(priv, data.server_ecdh_public, data.e2ee_session_id);
  setE2EESession(data.e2ee_session_id, aesKey, priv, data.server_ecdh_public);
}

export function resetE2EESession(): void {
  clearE2EESession();
  keyPair = null;
  handshakePromise = null;
}

export async function rehandshake(): Promise<void> {
  resetE2EESession();
  await ensureE2EESession();
}

export { getServerPublicB64 };
