const HKDF_INFO = new TextEncoder().encode('aastraa-e2ee-v1');

export type E2EEEnvelope = {
  e2ee: true;
  alg: string;
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
    (data as E2EEEnvelope).e2ee === true &&
    typeof (data as E2EEEnvelope).ct === 'string'
  );
}

export async function generateEcdhKeyPair(): Promise<CryptoKeyPair> {
  return crypto.subtle.generateKey(
    { name: 'ECDH', namedCurve: 'P-256' },
    true,
    ['deriveBits']
  );
}

export async function exportPublicKeySpkiB64(publicKey: CryptoKey): Promise<string> {
  const raw = await crypto.subtle.exportKey('spki', publicKey);
  return btoa(String.fromCharCode(...new Uint8Array(raw)));
}

async function hkdfSha256(
  ikm: Uint8Array,
  salt: Uint8Array,
  info: Uint8Array,
  length: number
): Promise<Uint8Array> {
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
  const debug = process.env.NEXT_PUBLIC_E2EE_DEBUG === 'true';
  if (debug && typeof performance !== 'undefined') {
    performance.mark('e2ee-decrypt-start');
  }
  const iv = Uint8Array.from(atob(envelope.iv), (c) => c.charCodeAt(0));
  const ct = Uint8Array.from(atob(envelope.ct), (c) => c.charCodeAt(0));
  const aad = new TextEncoder().encode(
    `${envelope.session_id}:${envelope.seq}:${envelope.nonce}:${envelope.ts}`
  );
  const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv, additionalData: aad }, aesKey, ct);
  if (debug && typeof performance !== 'undefined') {
    performance.mark('e2ee-decrypt-end');
    performance.measure('e2ee-decrypt', 'e2ee-decrypt-start', 'e2ee-decrypt-end');
  }
  return JSON.parse(new TextDecoder().decode(plain));
}

export async function encryptPayloadDemo(aesKey: CryptoKey, sessionId: string, obj: unknown, seq: number) {
  const nonceUuid = crypto.randomUUID();
  const ts = Date.now();
  const plaintext = new TextEncoder().encode(JSON.stringify(obj));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const aad = new TextEncoder().encode(`${sessionId}:${seq}:${nonceUuid}:${ts}`);
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: aad }, aesKey, plaintext);
  return {
    e2ee: true as const,
    alg: 'aes-256-gcm',
    session_id: sessionId,
    iv: btoa(String.fromCharCode(...iv)),
    ct: btoa(String.fromCharCode(...new Uint8Array(ct))),
    nonce: nonceUuid,
    ts,
    seq,
  };
}
