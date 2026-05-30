import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { isE2EEEnvelope } from '@/lib/e2ee/crypto';
import {
  decryptPublicResponse,
  ensurePublicE2EESession,
  getPublicSessionId,
  isPublicE2EEError,
  nextPublicSeq,
  rehandshakePublic,
  unwrapPublicApiPayload,
} from '@/lib/e2ee/publicE2ee';

type PublicAxiosConfig = InternalAxiosRequestConfig & {
  _e2eeRetry?: boolean;
  _decryptRetry?: boolean;
};

const publicApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1',
});

function isHandshakeRequest(config: PublicAxiosConfig): boolean {
  const url = config.url ?? '';
  return url.includes('/public/e2ee/handshake');
}

/** Public candidate interview APIs — must stay plaintext (TTS base64, multipart). */
const AI_SESSION_PUBLIC_PATH =
  /^\/recruitment\/ai-sessions\/(?:[^/]+\/(?:speak|questions\/next|start|preflight|feedback|complete-voice|questions\/skip|live(?:\/chunks|\/finalize-recording)?|tts\/\d+)|verify\/[^/]+)\/?$/;

function isE2eeExemptRequest(config: PublicAxiosConfig): boolean {
  const url = (config.url ?? '').replace(/\?.*$/, '');
  return AI_SESSION_PUBLIC_PATH.test(url);
}

publicApi.interceptors.request.use(async (config) => {
  if (isE2eeExemptRequest(config)) {
    return config;
  }
  await ensurePublicE2EESession();
  const sid = getPublicSessionId();
  if (sid) {
    config.headers = config.headers ?? {};
    config.headers['X-E2EE-Session'] = sid;
    config.headers['X-E2EE-Seq'] = String(nextPublicSeq());
  }
  return config;
});

publicApi.interceptors.response.use(
  async (response) => {
    const config = response.config as PublicAxiosConfig;
    if (isE2eeExemptRequest(config)) {
      return response;
    }
    if (response.data && isE2EEEnvelope(response.data)) {
      try {
        response.data = await unwrapPublicApiPayload(response.data);
      } catch {
        if (!config._decryptRetry && !isHandshakeRequest(config)) {
          config._decryptRetry = true;
          await rehandshakePublic();
          return publicApi.request(config);
        }
        throw new Error('Could not decrypt Astra voice response.');
      }
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as PublicAxiosConfig | undefined;
    if (!originalRequest) {
      return Promise.reject(error);
    }

    const status = error.response?.status;
    const body = error.response?.data;

    if (
      (status === 428 || status === 401) &&
      isPublicE2EEError(body) &&
      !originalRequest._e2eeRetry &&
      !isHandshakeRequest(originalRequest) &&
      !isE2eeExemptRequest(originalRequest)
    ) {
      originalRequest._e2eeRetry = true;
      try {
        await rehandshakePublic();
        return publicApi.request(originalRequest);
      } catch {
        return Promise.reject(error);
      }
    }

    if (body && isE2EEEnvelope(body)) {
      try {
        error.response!.data = await decryptPublicResponse(body);
      } catch {
        /* keep encrypted envelope */
      }
    }

    return Promise.reject(error);
  },
);

export default publicApi;
