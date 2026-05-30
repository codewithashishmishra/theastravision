"""Public stream of persisted Astra TTS clips ({session_id}_{n}.mp3)."""

from django.http import Http404, HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from recruitment.interview_storage import InterviewStorageService
from recruitment.live_auth import get_session_for_magic_token
from recruitment.models import AiInterviewMediaBlob, AiInterviewSession


class AiInterviewTtsStreamView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id, sequence: int):
        session = get_session_for_magic_token(session_id, request)
        blob = InterviewStorageService.get_blob(
            session.id,
            AiInterviewMediaBlob.KIND_ASTRA_TTS,
            question_order=int(sequence),
        )
        if blob:
            return InterviewStorageService.stream_blob_response(blob)
        raise Http404
