let sessionId: string | null = null;
let aesKey: CryptoKey | null = null;
let privateKey: CryptoKey | null = null;
let serverPublicB64: string | null = null;
let seq = 0;

export function getSessionId(): string | null {
  return sessionId;
}

export function getAesKey(): CryptoKey | null {
  return aesKey;
}

export function nextSeq(): number {
  seq += 1;
  return seq;
}

export function hasE2EESession(): boolean {
  return Boolean(sessionId && aesKey);
}

export function setE2EESession(
  id: string,
  key: CryptoKey,
  priv: CryptoKey,
  serverPub: string
): void {
  sessionId = id;
  aesKey = key;
  privateKey = priv;
  serverPublicB64 = serverPub;
  seq = 0;
}

export function getServerPublicB64(): string | null {
  return serverPublicB64;
}

export function getPrivateKey(): CryptoKey | null {
  return privateKey;
}

export function clearE2EESession(): void {
  sessionId = null;
  aesKey = null;
  privateKey = null;
  serverPublicB64 = null;
  seq = 0;
}
