"""Append frontend HTTP debug entries to debug.log (Super Admin toggle)."""

import json
import threading
from typing import Any

from django.conf import settings

_write_lock = threading.Lock()

_SENSITIVE_HEADER_KEYS = frozenset(
    k.lower() for k in ("authorization", "cookie", "set-cookie", "x-api-key")
)
_SENSITIVE_BODY_KEYS = frozenset(
    ("password", "api_key", "refresh", "access", "access_token", "refresh_token", "secret")
)


def _redact_headers(headers: Any) -> dict:
    if not isinstance(headers, dict):
        return {}
    out = {}
    for key, value in headers.items():
        if str(key).lower() in _SENSITIVE_HEADER_KEYS:
            out[key] = "[REDACTED]"
        else:
            out[key] = value
    return out


def _redact_body(body: Any) -> Any:
    if body is None:
        return None
    if isinstance(body, dict):
        out = {}
        for key, value in body.items():
            if str(key).lower() in _SENSITIVE_BODY_KEYS:
                out[key] = "[REDACTED]"
            elif isinstance(value, dict):
                out[key] = _redact_body(value)
            else:
                out[key] = value
        return out
    if isinstance(body, list):
        return [_redact_body(item) for item in body[:50]]
    return body


def _format_json(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, default=str)
    except (TypeError, ValueError):
        return str(value)


def append_frontend_debug_entry(payload: dict) -> None:
    direction = payload.get("direction", "unknown").upper()
    timestamp = payload.get("timestamp") or ""
    user_email = payload.get("user_email") or "unknown"
    roles = payload.get("roles") or []
    roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
    method = (payload.get("method") or "").upper()
    url = payload.get("url") or ""
    status = payload.get("status")
    headers = _redact_headers(payload.get("headers"))
    body = _redact_body(payload.get("body"))

    lines = []
    if direction == "REQUEST":
        lines.append("=" * 80)
        lines.append(f"[{timestamp}] REQUEST")
        lines.append(f"User: {user_email} | Roles: {roles_str}")
        lines.append(f"{method} {url}")
        lines.append(f"Headers: {_format_json(headers)}")
        lines.append(f"Body: {_format_json(body)}")
    else:
        status_part = f" {status}" if status is not None else ""
        lines.append("-" * 80)
        lines.append(f"[{timestamp}] RESPONSE{status_part}")
        lines.append(f"User: {user_email} | Roles: {roles_str}")
        lines.append(f"{method} {url}")
        lines.append(f"Headers: {_format_json(headers)}")
        lines.append(f"Body: {_format_json(body)}")
        if payload.get("error"):
            lines.append(f"Error: {payload.get('error')}")
        lines.append("=" * 80)

    text = "\n".join(lines) + "\n"
    log_path = settings.FRONTEND_DEBUG_LOG_PATH

    with _write_lock:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(text)
