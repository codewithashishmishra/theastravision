const HKDF_INFO = new TextEncoder().encode('aastraa-e2ee-v1');

export type E2EEEnvelope = {
  e2ee: true;
  session_id: string;
  iv: string;
  ct: string;
  nonce: string;
  ts: number;
  seq: number;
};

export function isE2EEEnvelope(data: unknown): data is E2EEEnvelope {
  return (
    typeof data === 'object' &&
    data !== null &&
    (data as E2EEEnvelope).e2ee === true
  );
}

async function hkdfSha256(ikm: Uint8Array, salt: Uint8Array, info: Uint8Array, length: number) {
  const key = await crypto.subtle.importKey('raw', ikm, 'HKDF', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt, info },
    key,
    length * 8
  );
  return new Uint8Array(bits);
}

export async function deriveAesKey(
  privateKey: CryptoKey,
  serverPublicSpkiB64: string,
  sessionId: string
): Promise<CryptoKey> {
  const der = Uint8Array.from(atob(serverPublicSpkiB64), (c) => c.charCodeAt(0));
  const serverPublic = await crypto.subtle.importKey(
    'spki',
    der,
    { name: 'ECDH', namedCurve: 'P-256' },
    false,
    []
  );
  const shared = await crypto.subtle.deriveBits(
    { name: 'ECDH', public: serverPublic },
    privateKey,
    256
  );
  const aesRaw = await hkdfSha256(
    new Uint8Array(shared),
    new TextEncoder().encode(sessionId),
    HKDF_INFO,
    32
  );
  return crypto.subtle.importKey('raw', aesRaw, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
}

export async function decryptEnvelope(aesKey: CryptoKey, envelope: E2EEEnvelope): Promise<unknown> {
  const iv = Uint8Array.from(atob(envelope.iv), (c) => c.charCodeAt(0));
  const ct = Uint8Array.from(atob(envelope.ct), (c) => c.charCodeAt(0));
  const aad = new TextEncoder().encode(
    `${envelope.session_id}:${envelope.seq}:${envelope.nonce}:${envelope.ts}`
  );
  const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv, additionalData: aad }, aesKey, ct);
  return JSON.parse(new TextDecoder().decode(plain));
}

export async function exportPublicKeySpkiB64(publicKey: CryptoKey): Promise<string> {
  const raw = await crypto.subtle.exportKey('spki', publicKey);
  return btoa(String.fromCharCode(...new Uint8Array(raw)));
}
