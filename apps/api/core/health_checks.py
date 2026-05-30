"""Platform module connectivity checks for Super Admin / IT Admin."""

from __future__ import annotations

import time

import requests
from django.conf import settings
from django.db import connection


def _entry(module: str, status: str, latency_ms: int = 0, message: str = '') -> dict:
    return {
        'module': module,
        'status': status,
        'latency_ms': latency_ms,
        'message': message,
    }


def check_database() -> dict:
    start = time.perf_counter()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        latency = int((time.perf_counter() - start) * 1000)
        return _entry('database', 'healthy', latency, 'PostgreSQL OK')
    except Exception as exc:
        return _entry('database', 'down', 0, str(exc)[:200])


def check_redis() -> dict:
    start = time.perf_counter()
    broker = getattr(settings, 'CELERY_BROKER_URL', '') or ''
    if not broker.startswith('redis'):
        return _entry('redis', 'skipped', 0, 'Non-Redis broker or not configured')
    try:
        import redis

        client = redis.from_url(broker)
        client.ping()
        latency = int((time.perf_counter() - start) * 1000)
        return _entry('redis', 'healthy', latency, 'Redis ping OK')
    except Exception as exc:
        return _entry('redis', 'down', 0, str(exc)[:200])


def check_celery() -> dict:
    start = time.perf_counter()
    try:
        from config.celery import app as celery_app

        insp = celery_app.control.inspect(timeout=2.0)
        ping = insp.ping() if insp else None
        latency = int((time.perf_counter() - start) * 1000)
        if ping:
            workers = len(ping)
            return _entry('celery', 'healthy', latency, f'{workers} worker(s) responding')
        return _entry('celery', 'degraded', latency, 'No Celery workers responded to ping')
    except Exception as exc:
        return _entry('celery', 'degraded', 0, str(exc)[:200])


def check_ai_service() -> dict:
    base = getattr(settings, 'AI_SERVICE_BASE_URL', '') or ''
    if not base:
        return _entry('ai_service', 'skipped', 0, 'AI_SERVICE_BASE_URL not set')
    url = f'{base.rstrip("/")}/health'
    start = time.perf_counter()
    try:
        resp = requests.get(url, timeout=5)
        latency = int((time.perf_counter() - start) * 1000)
        if resp.ok:
            return _entry('ai_service', 'healthy', latency, f'HTTP {resp.status_code}')
        return _entry('ai_service', 'degraded', latency, f'HTTP {resp.status_code}')
    except Exception as exc:
        return _entry('ai_service', 'down', 0, str(exc)[:200])


def check_smtp() -> dict:
    from core.email.smtp_client import build_smtp_connection, get_platform_smtp_config

    cfg = get_platform_smtp_config()
    if not cfg.get('host'):
        return _entry('smtp', 'skipped', 0, 'SMTP not configured')
    start = time.perf_counter()
    try:
        conn = build_smtp_connection()
        conn.open()
        conn.close()
        latency = int((time.perf_counter() - start) * 1000)
        return _entry('smtp', 'healthy', latency, f'Connected to {cfg.get("host")}')
    except Exception as exc:
        return _entry('smtp', 'down', 0, str(exc)[:200])


def check_imap() -> dict:
    from core.email.smtp_client import get_platform_imap_config, test_imap_connection

    cfg = get_platform_imap_config()
    if not cfg.get('host'):
        return _entry('imap', 'skipped', 0, 'IMAP not configured')
    try:
        result = test_imap_connection()
    except Exception as exc:
        return _entry('imap', 'down', 0, str(exc)[:200])
    status = 'healthy' if result.get('ok') else 'down'
    return _entry(
        'imap',
        status,
        result.get('latency_ms', 0),
        result.get('detail', ''),
    )


def check_clickhouse() -> dict:
    url = getattr(settings, 'CLICKHOUSE_URL', '') or ''
    if not url:
        return _entry('clickhouse', 'skipped', 0, 'CLICKHOUSE_URL not set')
    start = time.perf_counter()
    try:
        resp = requests.get(f'{url.rstrip("/")}/ping', timeout=3)
        latency = int((time.perf_counter() - start) * 1000)
        if resp.ok:
            return _entry('clickhouse', 'healthy', latency, 'Ping OK')
        return _entry('clickhouse', 'degraded', latency, f'HTTP {resp.status_code}')
    except Exception as exc:
        return _entry('clickhouse', 'down', 0, str(exc)[:200])


def run_all_module_health_checks() -> list[dict]:
    return [
        check_database(),
        check_redis(),
        check_celery(),
        check_ai_service(),
        check_smtp(),
        check_imap(),
        check_clickhouse(),
    ]
