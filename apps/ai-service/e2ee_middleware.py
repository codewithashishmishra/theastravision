"""FastAPI middleware: encrypt JSON responses when E2EE session header is present."""

from __future__ import annotations

import base64
import json
import os
from typing import Callable

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from e2ee_envelope import encrypt_envelope

E2EE_ENABLED = os.environ.get("E2EE_ENABLED", "True").lower() in ("true", "1", "yes")
DJANGO_API_URL = os.environ.get("DJANGO_API_URL", "http://127.0.0.1:8000").rstrip("/")
E2EE_INTERNAL_TOKEN = os.environ.get("E2EE_INTERNAL_TOKEN", os.environ.get("SECRET_KEY", "dev")[:32])

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


async def _load_aes_key(session_id: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"{DJANGO_API_URL}/api/v1/internal/e2ee/session/{session_id}/key/",
                headers={"X-Internal-Service-Token": E2EE_INTERNAL_TOKEN},
            )
            if res.status_code != 200:
                return None
            return base64.b64decode(res.json()["aes_key_b64"])
    except Exception:
        return None


async def _fetch_last_seq(session_id: str) -> int:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"{DJANGO_API_URL}/api/v1/internal/e2ee/session/{session_id}/",
                headers={"X-Internal-Service-Token": E2EE_INTERNAL_TOKEN},
            )
            if res.status_code != 200:
                return 0
            return int(res.json().get("last_seq", 0))
    except Exception:
        return 0


class E2EEResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not E2EE_ENABLED:
            return await call_next(request)
        if request.headers.get("x-internal-service") == "django":
            return await call_next(request)
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        session_id = request.headers.get("x-e2ee-session", "").strip()
        if not session_id:
            return JSONResponse(
                {"error": "e2ee_handshake_required", "code": "E2EE_HANDSHAKE_REQUIRED"},
                status_code=428,
            )

        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(content=body, status_code=response.status_code, headers=dict(response.headers))

        if isinstance(payload, dict) and payload.get("e2ee") is True:
            return JSONResponse(payload, status_code=response.status_code)

        aes_key = await _load_aes_key(session_id)
        if not aes_key:
            return JSONResponse(
                {"error": "e2ee_session_expired", "code": "E2EE_SESSION_EXPIRED"},
                status_code=401,
            )

        last_seq = await _fetch_last_seq(session_id)
        envelope = encrypt_envelope(aes_key, session_id, payload, last_seq + 1)
        headers = dict(response.headers)
        headers["X-E2EE"] = "1"
        headers.pop("content-length", None)
        return JSONResponse(envelope, status_code=response.status_code, headers=headers)
