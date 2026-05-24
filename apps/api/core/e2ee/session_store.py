"""Pluggable E2EE session store: PostgreSQL REDIS table or Redis."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.utils import timezone as dj_timezone

from core.gcm_crypto import unwrap_blob_at_rest, wrap_blob_at_rest

from .session_data import E2EESessionData

AT_REST_AAD = b"e2ee-session-v1"
SESSION_KEY_PREFIX = "e2ee:session:"


class SessionStore(ABC):
    @abstractmethod
    def get(self, session_id: str) -> E2EESessionData | None:
        ...

    @abstractmethod
    def set(self, session_id: str, data: E2EESessionData, ttl_seconds: int) -> None:
        ...

    @abstractmethod
    def delete(self, session_id: str) -> None:
        ...

    @abstractmethod
    def touch(self, session_id: str, data: E2EESessionData, ttl_seconds: int) -> None:
        ...


def _encrypt_at_rest(raw: bytes) -> bytes:
    return wrap_blob_at_rest(raw, AT_REST_AAD)


def _decrypt_at_rest(blob: bytes) -> bytes:
    return unwrap_blob_at_rest(blob, AT_REST_AAD)


class PostgresSessionStore(SessionStore):
    def get(self, session_id: str) -> E2EESessionData | None:
        from .models import Redis

        row = Redis.objects.filter(session_id=session_id).first()
        if not row:
            return None
        if row.expires_at <= dj_timezone.now():
            row.delete()
            return None
        try:
            raw = _decrypt_at_rest(bytes(row.payload))
            return E2EESessionData.from_json_bytes(raw)
        except Exception:
            row.delete()
            return None

    def set(self, session_id: str, data: E2EESessionData, ttl_seconds: int) -> None:
        from .models import Redis

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        payload = _encrypt_at_rest(data.to_json_bytes())
        Redis.objects.update_or_create(
            session_id=session_id,
            defaults={"payload": payload, "expires_at": expires_at},
        )

    def touch(self, session_id: str, data: E2EESessionData, ttl_seconds: int) -> None:
        self.set(session_id, data, ttl_seconds)

    def delete(self, session_id: str) -> None:
        from .models import Redis

        Redis.objects.filter(session_id=session_id).delete()


class RedisSessionStore(SessionStore):
    def __init__(self, redis_url: str, db: int = 2):
        import redis

        self._client = redis.from_url(redis_url, db=db, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"{SESSION_KEY_PREFIX}{session_id}"

    def get(self, session_id: str) -> E2EESessionData | None:
        raw_b64 = self._client.get(self._key(session_id))
        if not raw_b64:
            return None
        try:
            raw = _decrypt_at_rest(base64.b64decode(raw_b64))
            return E2EESessionData.from_json_bytes(raw)
        except Exception:
            self.delete(session_id)
            return None

    def set(self, session_id: str, data: E2EESessionData, ttl_seconds: int) -> None:
        blob = base64.b64encode(_encrypt_at_rest(data.to_json_bytes())).decode("ascii")
        self._client.setex(self._key(session_id), ttl_seconds, blob)

    def touch(self, session_id: str, data: E2EESessionData, ttl_seconds: int) -> None:
        self.set(session_id, data, ttl_seconds)

    def delete(self, session_id: str) -> None:
        self._client.delete(self._key(session_id))


_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        if getattr(settings, "REDIS_ALLOW", False):
            url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
            _store = RedisSessionStore(url, db=2)
        else:
            _store = PostgresSessionStore()
    return _store
