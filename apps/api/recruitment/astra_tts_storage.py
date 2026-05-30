"""Persist Astra TTS utterances as {session_id}_{sequence}.mp3 in PG (and optional filesystem)."""

from __future__ import annotations

import logging

from recruitment.interview_storage import InterviewStorageService
from recruitment.models import AiInterviewMediaBlob, AiInterviewSession

logger = logging.getLogger(__name__)


def next_tts_sequence(session: AiInterviewSession, *, preferred: int | None = None) -> int:
    """Allocate utterance index; uses question order when provided else increments counter."""
    flags = dict(session.proctor_flags or {})
    current = int(flags.get('tts_utterance_count', 0))
    if preferred is not None:
        seq = int(preferred)
        if seq > current:
            flags['tts_utterance_count'] = seq
            session.proctor_flags = flags
            session.save(update_fields=['proctor_flags', 'updated_at'])
        return seq
    seq = current + 1
    flags['tts_utterance_count'] = seq
    session.proctor_flags = flags
    session.save(update_fields=['proctor_flags', 'updated_at'])
    return seq


def persist_astra_tts(
    session: AiInterviewSession,
    audio_bytes: bytes,
    *,
    sequence: int | None = None,
) -> dict:
    """
    Store TTS MP3 as AiInterviewMediaBlob (kind=astra_tts) and optional filesystem copy.
    Returns metadata including filename like ``{session_uuid}_1.mp3``.
    """
    if not audio_bytes:
        raise ValueError('Cannot persist empty TTS audio')

    seq = next_tts_sequence(session, preferred=sequence)
    filename = f'{session.id}_{seq}.mp3'

    blob = InterviewStorageService.save_blob(
        session,
        AiInterviewMediaBlob.KIND_ASTRA_TTS,
        audio_bytes,
        content_type='audio/mpeg',
        question_order=seq,
    )

    rel_path = ''
    if not InterviewStorageService.use_pg_blobs():
        rel = f'interviews/{session.tenant_id}/{session.id}/{filename}'
        rel_path = InterviewStorageService.save_bytes(rel, audio_bytes)

    logger.info(
        'Persisted Astra TTS %s (%s bytes) session=%s seq=%s',
        filename,
        len(audio_bytes),
        session.id,
        seq,
    )
    return {
        'sequence': seq,
        'filename': filename,
        'blob_id': str(blob.id),
        'storage_path': rel_path or f'blob:{blob.id}',
    }
