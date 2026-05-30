"""Media streaming views for interview live watch and replay."""

from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from recruitment.interview_storage import InterviewStorageService
from recruitment.models import AiInterviewMediaBlob, AiInterviewMediaChunk, AiInterviewSession


class AiInterviewMediaStreamView(APIView):
    """Stream finalized blob or legacy filesystem recording."""

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, kind):
        tenant_id = getattr(request, 'tenant_id', None)
        try:
            session = AiInterviewSession.objects.get(pk=session_id, tenant_id=tenant_id)
        except AiInterviewSession.DoesNotExist:
            raise Http404

        question_order = request.query_params.get('question_order')
        q_order = int(question_order) if question_order else None

        if kind == AiInterviewMediaBlob.KIND_ASTRA_TTS and q_order is not None:
            blob = InterviewStorageService.get_blob(
                session.id, AiInterviewMediaBlob.KIND_ASTRA_TTS, question_order=q_order
            )
            if blob:
                return InterviewStorageService.stream_blob_response(blob)
            raise Http404

        if kind == AiInterviewMediaBlob.KIND_ANSWER_AUDIO and q_order is not None:
            blob = InterviewStorageService.get_blob(session.id, kind, question_order=q_order)
            if blob:
                return InterviewStorageService.stream_blob_response(blob)
            question = session.questions.filter(order=q_order).first()
            if question and question.audio_path:
                data, ct = InterviewStorageService.read_blob_or_path(
                    session, kind, question.audio_path, question_order=q_order
                )
                if data:
                    from django.http import HttpResponse
                    return HttpResponse(data, content_type=ct)
            raise Http404

        blob = InterviewStorageService.get_blob(session.id, kind)
        if blob:
            return InterviewStorageService.stream_blob_response(blob)

        path = ''
        if kind == AiInterviewMediaBlob.KIND_SESSION_COMPOSITE:
            path = session.session_recording_path or ''
        elif kind == AiInterviewMediaBlob.KIND_CAMERA:
            path = session.camera_recording_path or ''

        data, ct = InterviewStorageService.read_blob_or_path(session, kind, path)
        if not data:
            raise Http404
        from django.http import HttpResponse
        return HttpResponse(data, content_type=ct or 'video/webm')


class AiInterviewChunkStreamView(APIView):
    """Stream a single live chunk (HR authenticated)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, kind, sequence):
        tenant_id = getattr(request, 'tenant_id', None)
        try:
            session = AiInterviewSession.objects.get(pk=session_id, tenant_id=tenant_id)
        except AiInterviewSession.DoesNotExist:
            raise Http404
        chunk = InterviewStorageService.get_chunk(session.id, kind, int(sequence))
        if not chunk:
            raise Http404
        return InterviewStorageService.stream_chunk_response(chunk)
