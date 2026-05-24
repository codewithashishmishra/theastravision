"""Platform utilization sampling and cooldown state (Redis)."""

import json
from datetime import datetime, timedelta, timezone as dt_timezone

import psutil
import redis
from django.utils import timezone
from django.conf import settings

from core.platform_config import (
    cooldown_duration_seconds,
    cooldown_message,
    cpu_threshold,
    frontend_debug_enabled,
    ram_threshold,
    utilization_enabled,
)

REDIS_COOLDOWN_KEY = "platform:cooldown_until"
REDIS_METRICS_KEY = "platform:last_metrics"


def _redis_client():
    url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
    return redis.from_url(url, decode_responses=True)


def read_host_metrics():
    # Non-blocking read (interval=None uses last sample; avoids 500ms Celery worker stall)
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    return {
        "cpu_usage_percent": cpu_percent,
        "ram_usage_percent": memory.percent,
    }


def get_cooldown_until():
    """Return timezone-aware datetime or None if not in cooldown."""
    try:
        client = _redis_client()
        raw = client.get(REDIS_COOLDOWN_KEY)
    except redis.RedisError:
        return None
    if not raw:
        return None
    try:
        ts = float(raw)
        until = datetime.fromtimestamp(ts, tz=dt_timezone.utc)
        if until <= timezone.now():
            client.delete(REDIS_COOLDOWN_KEY)
            return None
        return until
    except (TypeError, ValueError):
        return None


def set_cooldown_until(dt):
    client = _redis_client()
    client.set(REDIS_COOLDOWN_KEY, str(dt.timestamp()))
    ttl = int((dt - timezone.now()).total_seconds()) + 60
    if ttl > 0:
        client.expire(REDIS_COOLDOWN_KEY, ttl)


def store_last_metrics(metrics: dict):
    try:
        client = _redis_client()
        client.setex(REDIS_METRICS_KEY, 120, json.dumps(metrics))
    except redis.RedisError:
        pass


def get_last_metrics():
    try:
        client = _redis_client()
        raw = client.get(REDIS_METRICS_KEY)
        if raw:
            return json.loads(raw)
    except (redis.RedisError, json.JSONDecodeError):
        pass
    return read_host_metrics()


def is_cooldown_active():
    return get_cooldown_until() is not None


def cooldown_retry_after_seconds():
    until = get_cooldown_until()
    if not until:
        return 0
    return max(0, int((until - timezone.now()).total_seconds()))


def build_cooldown_payload():
    until = get_cooldown_until()
    retry = cooldown_retry_after_seconds()
    return {
        "code": "PLATFORM_COOLDOWN",
        "message": cooldown_message(),
        "retry_after_seconds": retry,
        "cooldown_until": until.isoformat() if until else None,
    }


def activate_cooldown():
    duration = cooldown_duration_seconds()
    until = timezone.now() + timedelta(seconds=duration)
    existing = get_cooldown_until()
    if existing and existing > until:
        until = existing
    set_cooldown_until(until)
    return until


def sample_utilization_and_maybe_cooldown():
    metrics = read_host_metrics()
    store_last_metrics(metrics)

    if not utilization_enabled():
        return {"triggered": False, "metrics": metrics, "disabled": True}

    cpu_limit = cpu_threshold()
    ram_limit = ram_threshold()

    if (
        metrics["cpu_usage_percent"] >= cpu_limit
        and metrics["ram_usage_percent"] >= ram_limit
    ):
        # Dev machines often sit above thresholds due to local tooling; still record metrics.
        if getattr(settings, "DEBUG", False):
            return {"triggered": False, "metrics": metrics, "skipped_cooldown": True}
        activate_cooldown()
        return {"triggered": True, "metrics": metrics}

    return {"triggered": False, "metrics": metrics}


def build_status_payload():
    metrics = get_last_metrics()
    until = get_cooldown_until()
    active = until is not None
    retry = cooldown_retry_after_seconds()
    cpu_limit = cpu_threshold()
    ram_limit = ram_threshold()
    return {
        "cooldown_active": active,
        "cooldown_until": until.isoformat() if until else None,
        "retry_after_seconds": retry,
        "cpu_percent": metrics.get("cpu_usage_percent", 0),
        "ram_percent": metrics.get("ram_usage_percent", 0),
        "cpu_threshold": cpu_limit,
        "ram_threshold": ram_limit,
        "utilization_enabled": utilization_enabled(),
        "near_threshold": (
            metrics.get("cpu_usage_percent", 0) >= cpu_limit * 0.9
            or metrics.get("ram_usage_percent", 0) >= ram_limit * 0.9
        ),
        "frontend_debug_enabled": frontend_debug_enabled(),
    }
