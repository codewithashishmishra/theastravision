"""Auth helpers for public candidate live endpoints."""

from __future__ import annotations

import uuid

from rest_framework.exceptions import PermissionDenied

from recruitment.models import AiInterviewSession


def _parse_uuid(value: str):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def get_session_for_magic_token(session_id, request) -> AiInterviewSession:
    """Validate session id + magic token from header or query/body."""
    token_raw = (
        request.headers.get('X-Interview-Token')
        or request.query_params.get('magic_token')
        or request.data.get('magic_token')
    )
    if not token_raw:
        raise PermissionDenied('Interview token required.')
    token_uuid = _parse_uuid(token_raw)
    if not token_uuid:
        raise PermissionDenied('Invalid interview token.')
    try:
        return AiInterviewSession.objects.get(pk=session_id, magic_token=token_uuid)
    except AiInterviewSession.DoesNotExist:
        raise PermissionDenied('Invalid session or token.')
