"""Encrypt JSON API responses with session-bound AES-256-GCM envelopes."""

from __future__ import annotations

import json
import re

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.utils.deprecation import MiddlewareMixin

from core.e2ee.services import encrypt_response_for_session


# Public AI interview routes carry large TTS/base64 payloads — keep plaintext JSON.
_AI_SESSION_PUBLIC_PATH = re.compile(
    r"^/api/v1/recruitment/ai-sessions/[^/]+/(?:speak|questions/next|verify|start|preflight|"
    r"feedback|complete-voice|questions/skip|live(?:/chunks|/finalize-recording)?|tts/\d+)/?$"
)


class E2EEResponseMiddleware(MiddlewareMixin):
    TRACKER_BROWSER_AUTH_EXEMPT_PATHS = {
        "/api/v1/tracker/auth/browser",
        "/api/v1/auth/login/password",
        "/api/v1/auth/totp/verify-login",
        "/api/v1/tracker/auth/bootstrap",
    }

    EXEMPT_PREFIXES = (
        "/admin/",
        "/static/",
        "/media/",
        "/health",
    )

    def _enabled(self) -> bool:
        return getattr(settings, "E2EE_ENABLED", False)

    def _is_exempt(self, path: str) -> bool:
        norm = path.rstrip("/")
        if norm == "/api/v1/public/e2ee/handshake":
            return True
        if norm in self.TRACKER_BROWSER_AUTH_EXEMPT_PATHS:
            return True
        if path.startswith("/api/v1/internal/e2ee/"):
            return True
        if _AI_SESSION_PUBLIC_PATH.match(path.rstrip("/")):
            return True
        # List/detail without sub-action still uses E2EE; verify token is under verify/{token}
        if re.match(r"^/api/v1/recruitment/ai-sessions/verify/[^/]+/?$", path.rstrip("/")):
            return True
        return any(path.startswith(p) for p in self.EXEMPT_PREFIXES)

    def _wants_json(self, request) -> bool:
        accept = request.META.get("HTTP_ACCEPT", "")
        if "application/json" in accept or accept == "":
            return True
        content_type = request.META.get("CONTENT_TYPE", "")
        return "application/json" in content_type

    def _is_api_json_route(self, request) -> bool:
        if request.method == "OPTIONS":
            return False
        if request.META.get("HTTP_X_INTERNAL_SERVICE") == "django":
            return False
        path = request.path
        if self._is_exempt(path):
            return False
        return path.startswith("/api/") and self._wants_json(request)

    def process_request(self, request):
        if not self._enabled():
            return None
        if not self._is_api_json_route(request):
            return None
        session_id = request.META.get("HTTP_X_E2EE_SESSION", "").strip()
        if not session_id:
            return JsonResponse(
                {
                    "error": "e2ee_handshake_required",
                    "code": "E2EE_HANDSHAKE_REQUIRED",
                },
                status=428,
            )
        request.e2ee_session_id = session_id
        seq_header = request.META.get("HTTP_X_E2EE_SEQ", "").strip()
        request.e2ee_request_seq = int(seq_header) if seq_header.isdigit() else None
        return None

    def process_response(self, request, response):
        if not self._enabled():
            return response
        if isinstance(response, StreamingHttpResponse):
            return response
        if self._is_exempt(request.path):
            return response
        content_type = response.get("Content-Type", "")
        if "application/json" not in content_type:
            return response
        session_id = getattr(request, "e2ee_session_id", None) or request.META.get(
            "HTTP_X_E2EE_SESSION", ""
        ).strip()
        if not session_id:
            return response
        try:
            body = json.loads(response.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return response
        if isinstance(body, dict) and body.get("e2ee") is True:
            return response
        request_seq = getattr(request, "e2ee_request_seq", None)
        envelope = encrypt_response_for_session(session_id, body, request_seq)
        if not envelope:
            return JsonResponse(
                {"error": "e2ee_session_expired", "code": "E2EE_SESSION_EXPIRED"},
                status=401,
            )
        response.content = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
        response["Content-Type"] = "application/json"
        response["X-E2EE"] = "1"
        if "Content-Length" in response:
            del response["Content-Length"]
        return response
