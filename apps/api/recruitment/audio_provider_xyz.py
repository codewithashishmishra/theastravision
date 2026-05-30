"""Audio provider adapter for self-hosted Kokoro/Whisper (WebSocket or HTTP)."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


class AudioProviderError(RuntimeError):
    """Raised when the voice provider cannot serve audio/transcript."""


@dataclass
class XyzAudioProvider:
    url: str
    http_base: str
    api_key: str
    salad_api_key: str = ''
    timeout_seconds: int = 15
    heartbeat_seconds: int = 10

    @classmethod
    def from_settings(cls) -> 'XyzAudioProvider':
        return cls(
            url=getattr(settings, 'XYZ_AUDIO_WS_URL', '').strip(),
            http_base=getattr(settings, 'XYZ_AUDIO_HTTP_BASE_URL', '').strip().rstrip('/'),
            api_key=getattr(settings, 'XYZ_AUDIO_API_KEY', '').strip(),
            salad_api_key=getattr(settings, 'XYZ_SALAD_API_KEY', '').strip(),
            timeout_seconds=int(getattr(settings, 'XYZ_AUDIO_TIMEOUT_SECONDS', 15)),
            heartbeat_seconds=int(getattr(settings, 'XYZ_AUDIO_HEARTBEAT_SECONDS', 10)),
        )

    def _request_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.salad_api_key:
            headers['Salad-Api-Key'] = self.salad_api_key
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    async def _send_ws_request(self, payload: dict) -> dict:
        if not self.url:
            raise AudioProviderError('XYZ_AUDIO_WS_URL is not configured.')
        try:
            import websockets
        except Exception as exc:
            raise AudioProviderError('websockets dependency missing for xyz audio provider.') from exc

        headers = self._request_headers() or None
        try:
            async with websockets.connect(
                self.url,
                additional_headers=headers,
                open_timeout=self.timeout_seconds,
                ping_interval=self.heartbeat_seconds,
                close_timeout=self.timeout_seconds,
            ) as ws:
                await ws.send(json.dumps(payload))
                raw = await asyncio.wait_for(ws.recv(), timeout=self.timeout_seconds)
        except Exception as exc:
            logger.exception('XYZ websocket request failed')
            raise AudioProviderError(f'xyz websocket failure: {exc}') from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AudioProviderError('xyz websocket returned invalid JSON.') from exc
        if parsed.get('error'):
            raise AudioProviderError(str(parsed['error']))
        return parsed

    def _http_tts_sync(self, text: str, *, voice: str) -> tuple[bytes, str]:
        import requests

        response = requests.post(
            f'{self.http_base}/api/v1/tts',
            headers=self._request_headers(),
            json={'text': text[:3000], 'voice': voice},
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise AudioProviderError(f'xyz HTTP TTS failed: {response.status_code} {response.text[:200]}')
        mime = response.headers.get('content-type') or 'audio/mpeg'
        return response.content, mime

    def _http_stt_sync(self, audio_bytes: bytes, *, filename: str) -> dict:
        import requests

        response = requests.post(
            f'{self.http_base}/api/v1/transcribe',
            headers=self._request_headers(),
            files={'audio': (filename, audio_bytes)},
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise AudioProviderError(f'xyz HTTP STT failed: {response.status_code} {response.text[:200]}')
        parsed = response.json()
        return {
            'text': parsed.get('text', ''),
            'detected_language': parsed.get('detected_language', 'en'),
        }

    async def synthesize_tts(self, text: str, *, voice: str = 'astra') -> tuple[bytes, str]:
        if self.http_base:
            return await asyncio.to_thread(self._http_tts_sync, text, voice=voice)
        payload = {'event': 'tts', 'voice': voice, 'text': text[:3000]}
        parsed = await self._send_ws_request(payload)
        audio_b64 = parsed.get('audio_base64') or ''
        if not audio_b64:
            raise AudioProviderError('xyz websocket returned empty TTS audio.')
        try:
            audio = base64.b64decode(audio_b64)
        except Exception as exc:
            raise AudioProviderError('xyz websocket returned invalid base64 audio.') from exc
        return audio, parsed.get('mime') or 'audio/mpeg'

    async def transcribe_audio(self, audio_bytes: bytes, *, filename: str = 'audio.webm') -> dict:
        if self.http_base:
            return await asyncio.to_thread(self._http_stt_sync, audio_bytes, filename=filename)
        payload = {
            'event': 'stt',
            'filename': filename,
            'audio_base64': base64.b64encode(audio_bytes).decode('ascii'),
        }
        parsed = await self._send_ws_request(payload)
        return {
            'text': parsed.get('text', ''),
            'detected_language': parsed.get('detected_language', 'en'),
        }
