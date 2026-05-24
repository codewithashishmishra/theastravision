"""HTTP client for the FastAPI ai-service."""

from __future__ import annotations

import logging

import requests
from django.conf import settings

from core.models import EnvConfiguration

logger = logging.getLogger(__name__)


def get_ai_service_base_url() -> str:
    return getattr(settings, 'AI_SERVICE_BASE_URL', 'http://127.0.0.1:8001').rstrip('/')


def get_openai_credentials() -> dict:
    cfg = EnvConfiguration.get_cached_config('AI') or {}
    return {
        'api_key': cfg.get('api_key', ''),
        'model': cfg.get('model', 'gpt-5.4-mini'),
        'provider': cfg.get('provider', 'openai'),
    }


def _headers() -> dict:
    creds = get_openai_credentials()
    headers = {
        'Content-Type': 'application/json',
        'X-Internal-Service': 'django',
    }
    if creds.get('api_key'):
        headers['X-OpenAI-Api-Key'] = creds['api_key']
        headers['X-OpenAI-Model'] = creds.get('model', 'gpt-5.4-mini')
    return headers


def ai_post(path: str, json_payload: dict | None = None, files=None, timeout: int = 120) -> dict:
    url = f"{get_ai_service_base_url()}{path}"
    try:
        if files:
            response = requests.post(url, files=files, data=json_payload or {}, headers={
                k: v for k, v in _headers().items() if k != 'Content-Type'
            }, timeout=timeout)
        else:
            response = requests.post(url, json=json_payload or {}, headers=_headers(), timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.exception('AI service call failed: %s', path)
        raise RuntimeError(f'AI service error: {exc}') from exc


def ai_get_bytes(path: str, json_payload: dict, timeout: int = 60) -> bytes:
    url = f"{get_ai_service_base_url()}{path}"
    response = requests.post(url, json=json_payload, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    return response.content
