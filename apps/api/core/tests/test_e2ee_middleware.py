"""E2EE middleware and handshake integration tests."""

import json

from django.test import Client, TestCase, override_settings

from core.e2ee.ecdh import derive_shared_aes_key, export_public_spki_b64, generate_ephemeral_keypair
from core.e2ee.envelope import decrypt_envelope
from core.e2ee.services import create_handshake_session
from core.middleware.e2ee_response_middleware import E2EEResponseMiddleware


@override_settings(E2EE_ENABLED=True, REDIS_ALLOW=False)
class E2EEMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _handshake(self):
        priv, pub = generate_ephemeral_keypair()
        client_pub = export_public_spki_b64(pub)
        res = self.client.post(
            "/api/v1/public/e2ee/handshake/",
            data={"client_ecdh_public": client_pub, "client_type": "public"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.content)
        aes_key = derive_shared_aes_key(priv, body["server_ecdh_public"], body["session_id"])
        return body["session_id"], aes_key

    def test_handshake_returns_plaintext(self):
        session_id, _ = self._handshake()
        self.assertTrue(session_id)

    def test_json_without_session_returns_428(self):
        res = self.client.get("/api/v1/feature-flags/", HTTP_ACCEPT="application/json")
        self.assertEqual(res.status_code, 428)
        body = json.loads(res.content)
        self.assertEqual(body["code"], "E2EE_HANDSHAKE_REQUIRED")

    def test_json_with_session_is_encrypted(self):
        session_id, aes_key = self._handshake()
        res = self.client.get(
            "/api/v1/feature-flags/",
            HTTP_ACCEPT="application/json",
            HTTP_X_E2EE_SESSION=session_id,
            HTTP_X_E2EE_SEQ="1",
        )
        self.assertIn(res.status_code, (200, 401, 403))
        body = json.loads(res.content)
        self.assertTrue(body.get("e2ee"))
        decrypted = decrypt_envelope(aes_key, body)
        self.assertIsInstance(decrypted, (dict, list))

    def test_speak_route_exempt_from_e2ee(self):
        mw = E2EEResponseMiddleware(lambda request: None)
        path = "/api/v1/recruitment/ai-sessions/915092df-bcfc-43e8-aea6-f1f8424234ae/speak/"
        self.assertTrue(mw._is_exempt(path))
        self.assertTrue(mw._is_exempt(path.rstrip("/")))

    def test_tracker_browser_login_exempt_from_e2ee(self):
        mw = E2EEResponseMiddleware(lambda request: None)
        self.assertTrue(mw._is_exempt("/api/v1/tracker/auth/browser/"))
        self.assertTrue(mw._is_exempt("/api/v1/auth/login/password/"))
        self.assertTrue(mw._is_exempt("/api/v1/auth/totp/verify-login/"))
        self.assertTrue(mw._is_exempt("/api/v1/tracker/auth/bootstrap/"))

    def test_create_handshake_session_service(self):
        priv, pub = generate_ephemeral_keypair()
        out = create_handshake_session(export_public_spki_b64(pub), client_type="public")
        self.assertIn("session_id", out)
        self.assertIn("server_ecdh_public", out)
