from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import BinaryIO, Iterator

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from django.http import StreamingHttpResponse
from django.utils import timezone

from recruitment.models import (
    AiInterviewMediaBlob,
    AiInterviewMediaChunk,
    AiInterviewSession,
    TenantRecruitmentSettings,
)


class InterviewStorageService:
    @classmethod
    def get_storage(cls):
        if getattr(settings, 'ALLOW_S3', False):
            return default_storage
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        return FileSystemStorage(location=str(media_root))

    @classmethod
    def use_pg_blobs(cls) -> bool:
        return not getattr(settings, 'ALLOW_S3', False)

    @classmethod
    def blob_expires_at(cls, session: AiInterviewSession):
        policy = TenantRecruitmentSettings.get_for_tenant(session.tenant_id)
        days = policy.interview_recording_retention_days or 15
        return timezone.now() + timedelta(days=days)

    @classmethod
    def save_bytes(cls, rel_path: str, data: bytes) -> str:
        storage = cls.get_storage()
        return storage.save(rel_path, ContentFile(data))

    @classmethod
    def save_upload(cls, rel_path: str, uploaded_file) -> str:
        storage = cls.get_storage()
        return storage.save(rel_path, uploaded_file)

    @classmethod
    def open_path(cls, rel_path: str):
        storage = cls.get_storage()
        return storage.open(rel_path, 'rb')

    @classmethod
    def delete_path(cls, rel_path: str) -> None:
        if not rel_path:
            return
        storage = cls.get_storage()
        if storage.exists(rel_path):
            storage.delete(rel_path)

    # --- PostgreSQL chunk / blob storage ---

    @classmethod
    def save_chunk(
        cls,
        session: AiInterviewSession,
        kind: str,
        sequence: int,
        data: bytes,
        content_type: str = 'video/webm',
    ) -> AiInterviewMediaChunk:
        chunk, _ = AiInterviewMediaChunk.objects.update_or_create(
            session=session,
            kind=kind,
            sequence=sequence,
            defaults={
                'content_type': content_type,
                'data': data,
                'byte_size': len(data),
            },
        )
        return chunk

    @classmethod
    def list_chunks(
        cls,
        session_id,
        kind: str | None = None,
        since_sequence: int = 0,
    ) -> list[AiInterviewMediaChunk]:
        qs = AiInterviewMediaChunk.objects.filter(session_id=session_id, sequence__gt=since_sequence)
        if kind:
            qs = qs.filter(kind=kind)
        return list(qs.order_by('kind', 'sequence'))

    @classmethod
    def get_chunk(cls, session_id, kind: str, sequence: int) -> AiInterviewMediaChunk | None:
        return AiInterviewMediaChunk.objects.filter(
            session_id=session_id, kind=kind, sequence=sequence
        ).first()

    @classmethod
    def save_blob(
        cls,
        session: AiInterviewSession,
        kind: str,
        data: bytes,
        *,
        content_type: str = 'application/octet-stream',
        question_order: int | None = None,
    ) -> AiInterviewMediaBlob:
        expires = cls.blob_expires_at(session)
        blob, _ = AiInterviewMediaBlob.objects.update_or_create(
            session=session,
            kind=kind,
            question_order=question_order,
            defaults={
                'content_type': content_type,
                'data': data,
                'byte_size': len(data),
                'expires_at': expires,
            },
        )
        return blob

    @classmethod
    def get_blob(
        cls,
        session_id,
        kind: str,
        question_order: int | None = None,
    ) -> AiInterviewMediaBlob | None:
        qs = AiInterviewMediaBlob.objects.filter(session_id=session_id, kind=kind)
        if question_order is not None:
            qs = qs.filter(question_order=question_order)
        return qs.first()

    @classmethod
    def merge_chunks_to_blob(
        cls,
        session: AiInterviewSession,
        kind: str,
        content_type: str = 'video/webm',
    ) -> AiInterviewMediaBlob | None:
        chunks = AiInterviewMediaChunk.objects.filter(
            session=session, kind=kind
        ).order_by('sequence')
        if not chunks.exists():
            return None
        merged = b''.join(c.data for c in chunks)
        blob = cls.save_blob(session, kind, merged, content_type=content_type)
        chunks.delete()
        return blob

    @classmethod
    def finalize_session_recordings(cls, session: AiInterviewSession) -> dict:
        """Merge live chunks into final blobs for session composite and camera."""
        result = {}
        for kind in (
            AiInterviewMediaChunk.KIND_SESSION_COMPOSITE,
            AiInterviewMediaChunk.KIND_CAMERA,
        ):
            blob = cls.merge_chunks_to_blob(session, kind, content_type='video/webm')
            if blob:
                result[kind] = str(blob.id)
                if kind == AiInterviewMediaChunk.KIND_SESSION_COMPOSITE:
                    session.session_recording_path = f'blob:{blob.id}'
                elif kind == AiInterviewMediaChunk.KIND_CAMERA:
                    session.camera_recording_path = f'blob:{blob.id}'
        return result

    @classmethod
    def save_answer_audio_blob(
        cls,
        session: AiInterviewSession,
        question_order: int,
        data: bytes,
        content_type: str = 'audio/webm',
    ) -> AiInterviewMediaBlob:
        return cls.save_blob(
            session,
            AiInterviewMediaBlob.KIND_ANSWER_AUDIO,
            data,
            content_type=content_type,
            question_order=question_order,
        )

    @classmethod
    def stream_blob_response(cls, blob: AiInterviewMediaBlob) -> StreamingHttpResponse:
        def iterator() -> Iterator[bytes]:
            yield bytes(blob.data)

        resp = StreamingHttpResponse(iterator(), content_type=blob.content_type)
        resp['Content-Length'] = blob.byte_size
        resp['Accept-Ranges'] = 'bytes'
        return resp

    @classmethod
    def stream_chunk_response(cls, chunk: AiInterviewMediaChunk) -> StreamingHttpResponse:
        def iterator() -> Iterator[bytes]:
            yield bytes(chunk.data)

        resp = StreamingHttpResponse(iterator(), content_type=chunk.content_type)
        resp['Content-Length'] = chunk.byte_size
        return resp

    @classmethod
    def read_blob_or_path(
        cls,
        session: AiInterviewSession,
        kind: str,
        path: str = '',
        question_order: int | None = None,
    ) -> tuple[bytes | None, str]:
        """Return (bytes, content_type) from PG blob or filesystem path."""
        blob = cls.get_blob(session.id, kind, question_order=question_order)
        if blob:
            return bytes(blob.data), blob.content_type
        if path and path.startswith('blob:'):
            blob_id = path.replace('blob:', '', 1)
            try:
                b = AiInterviewMediaBlob.objects.get(pk=blob_id, session_id=session.id)
                return bytes(b.data), b.content_type
            except AiInterviewMediaBlob.DoesNotExist:
                return None, 'application/octet-stream'
        if path:
            try:
                with cls.open_path(path) as f:
                    return f.read(), 'application/octet-stream'
            except Exception:
                return None, 'application/octet-stream'
        return None, 'application/octet-stream'
