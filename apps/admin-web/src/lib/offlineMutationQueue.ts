import type { InternalAxiosRequestConfig } from 'axios';

const DB_NAME = 'aastraa_offline';
const STORE_NAME = 'mutations';
const DB_VERSION = 1;
const LS_KEY = 'aastraa_offline_queue';
const LS_MAX = 50;
const MAX_BODY_BYTES = 512_000;

export type QueuedMutation = {
  id: string;
  method: string;
  url: string;
  body: string | null;
  headers: Record<string, string>;
  createdAt: string;
};

const MUTATING = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB unavailable'));
      return;
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onerror = () => reject(req.error);
    req.onsuccess = () => resolve(req.result);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
  });
}

function readLocalQueue(): QueuedMutation[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as QueuedMutation[];
  } catch {
    return [];
  }
}

function writeLocalQueue(items: QueuedMutation[]) {
  localStorage.setItem(LS_KEY, JSON.stringify(items.slice(-LS_MAX)));
}

async function idbAdd(item: QueuedMutation): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put(item);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function idbAll(): Promise<QueuedMutation[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).getAll();
    req.onsuccess = () => {
      const items = (req.result as QueuedMutation[]).sort(
        (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
      );
      resolve(items);
    };
    req.onerror = () => reject(req.error);
  });
}

async function idbRemove(id: string): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

function serializeBody(data: unknown): string | null {
  if (data === undefined || data === null) return null;
  if (typeof data === 'string') return data;
  return JSON.stringify(data);
}

function isMultipart(config: InternalAxiosRequestConfig): boolean {
  const headers = config.headers;
  const ct =
    (typeof headers?.get === 'function'
      ? headers.get('Content-Type')
      : (headers as Record<string, string>)?.['Content-Type']) ?? '';
  return String(ct).includes('multipart/form-data');
}

export async function enqueueMutation(config: InternalAxiosRequestConfig): Promise<string | null> {
  const method = (config.method ?? 'get').toUpperCase();
  if (!MUTATING.has(method)) return null;
  if (isMultipart(config)) return null;

  const body = serializeBody(config.data);
  if (body && body.length > MAX_BODY_BYTES) return null;

  const base = config.baseURL ?? '';
  const url = `${base}${config.url ?? ''}`.replace(/([^:]\/)\/+/g, '$1');

  const item: QueuedMutation = {
    id: crypto.randomUUID(),
    method,
    url,
    body,
    headers: {
      'Content-Type': 'application/json',
    },
    createdAt: new Date().toISOString(),
  };

  try {
    await idbAdd(item);
  } catch {
    const q = readLocalQueue();
    q.push(item);
    writeLocalQueue(q);
  }
  return item.id;
}

export async function getPendingCount(): Promise<number> {
  try {
    const items = await idbAll();
    return items.length;
  } catch {
    return readLocalQueue().length;
  }
}

export async function getPendingMutations(): Promise<QueuedMutation[]> {
  try {
    return await idbAll();
  } catch {
    return readLocalQueue();
  }
}

export type FlushResult = { synced: number; failed: number };

export async function flushOfflineQueue(
  replay: (item: QueuedMutation) => Promise<void>
): Promise<FlushResult> {
  const items = await getPendingMutations();
  let synced = 0;
  let failed = 0;

  for (const item of items) {
    try {
      await replay(item);
      try {
        await idbRemove(item.id);
      } catch {
        writeLocalQueue(readLocalQueue().filter((x) => x.id !== item.id));
      }
      synced += 1;
    } catch {
      failed += 1;
    }
  }
  return { synced, failed };
}
