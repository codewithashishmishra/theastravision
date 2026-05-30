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


def pre_generate_campaign_questions(
    campaign_id: str,
    job_title: str,
    jd_text: str,
    *,
    timeout: int = 120,
) -> list[dict]:
    payload = {
        'campaign_id': campaign_id,
        'job_title': job_title,
        'jd_text': jd_text,
        'count': 5,
    }
    result = ai_post('/api/v1/ai/recruitment/campaign-baseline-questions', payload, timeout=timeout)
    return list(result.get('questions') or [])


def pre_generate_candidate_questions(
    candidate_id: str,
    campaign_id: str | None,
    job_title: str,
    jd_text: str,
    resume_text: str,
    experience_summary: str,
    *,
    timeout: int = 120,
) -> list[dict]:
    payload = {
        'candidate_id': candidate_id,
        'campaign_id': campaign_id,
        'job_title': job_title,
        'jd_text': jd_text,
        'resume_text': resume_text,
        'experience_summary': experience_summary,
        'count': 5,
    }
    result = ai_post('/api/v1/ai/recruitment/candidate-adaptive-questions', payload, timeout=timeout)
    return list(result.get('questions') or [])


def semantic_evaluate_answer(
    question: str,
    benchmark_answer: str,
    candidate_answer: str,
    *,
    timeout: int = 120,
) -> dict:
    payload = {
        'question': question,
        'benchmark_answer': benchmark_answer,
        'candidate_answer': candidate_answer,
    }
    return ai_post('/api/v1/ai/recruitment/semantic-evaluation', payload, timeout=timeout)


def generate_conversation_message(
    *,
    question_text: str,
    candidate_name: str,
    job_title: str,
    context: str = 'interviewer_turn',
    timeout: int = 60,
) -> str:
    payload = {
        'question_text': question_text,
        'candidate_name': candidate_name,
        'job_title': job_title,
        'context': context,
    }
    result = ai_post('/api/v1/ai/recruitment/conversation-message', payload, timeout=timeout)
    return (result.get('message') or '').strip()
