"""Push real-time interview events to WebSocket subscribers."""

from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


def _group_name(session_id) -> str:
    return f'interview_session_{session_id}'


def _send(session_id, event_type: str, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        _group_name(session_id),
        {
            'type': event_type,
            **payload,
        },
    )


def emit_transcript_segment(
    session_id,
    *,
    speaker: str,
    text: str,
    question_order: int | None = None,
    is_final: bool = True,
) -> None:
    _send(
        session_id,
        'transcript_segment',
        {
            'speaker': speaker,
            'text': text,
            'ts': timezone.now().isoformat(),
            'question_order': question_order,
            'is_final': is_final,
        },
    )


def emit_session_state(
    session_id,
    *,
    status: str,
    current_question_index: int = 0,
    phase: str = '',
) -> None:
    _send(
        session_id,
        'session_state',
        {
            'status': status,
            'current_question_index': current_question_index,
            'phase': phase,
        },
    )


def emit_chunk_available(
    session_id,
    *,
    kind: str,
    sequence: int,
    byte_size: int,
    created_at: str | None = None,
) -> None:
    _send(
        session_id,
        'chunk_available',
        {
            'kind': kind,
            'sequence': sequence,
            'byte_size': byte_size,
            'created_at': created_at or timezone.now().isoformat(),
        },
    )


def emit_concern_flagged(session_id, *, note: str, flagged_by: str = '') -> None:
    _send(
        session_id,
        'concern_flagged',
        {'note': note, 'flagged_by': flagged_by, 'ts': timezone.now().isoformat()},
    )


def emit_session_ended(session_id, *, status: str) -> None:
    _send(
        session_id,
        'session_ended',
        {'status': status, 'ts': timezone.now().isoformat()},
    )
