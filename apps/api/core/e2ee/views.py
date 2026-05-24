"""Public E2EE handshake and internal session lookup endpoints."""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from .services import create_handshake_session, export_session_aes_key_b64, get_session_for_internal


class E2EEHandshakeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        client_pub = request.data.get("client_ecdh_public") or request.data.get("client_pub")
        if not client_pub:
            return Response({"error": "client_ecdh_public required"}, status=400)
        client_type = request.data.get("client_type") or "public"
        payload = create_handshake_session(client_pub, client_type=client_type)
        return Response(payload)


class InternalE2EESessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id: str):
        expected = getattr(settings, "E2EE_INTERNAL_TOKEN", "") or settings.SECRET_KEY[:32]
        token = request.headers.get("X-Internal-Service-Token", "")
        if not token or token != expected:
            return Response({"error": "Forbidden"}, status=403)
        info = get_session_for_internal(session_id)
        if not info:
            return Response({"error": "Not found"}, status=404)
        return Response(info)


class InternalE2EESessionKeyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id: str):
        expected = getattr(settings, "E2EE_INTERNAL_TOKEN", "") or settings.SECRET_KEY[:32]
        token = request.headers.get("X-Internal-Service-Token", "")
        if not token or token != expected:
            return Response({"error": "Forbidden"}, status=403)
        key_b64 = export_session_aes_key_b64(session_id)
        if not key_b64:
            return Response({"error": "Not found"}, status=404)
        return Response({"aes_key_b64": key_b64})
