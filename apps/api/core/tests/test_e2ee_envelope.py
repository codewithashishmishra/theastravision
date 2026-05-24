"""Envelope encrypt/decrypt and replay protection tests."""

import time

from django.test import SimpleTestCase

from core.e2ee.envelope import (
    advance_replay_state,
    decrypt_envelope,
    encrypt_envelope,
    validate_replay_state,
)
from core.gcm_crypto import generate_data_key


class E2EEEnvelopeTests(SimpleTestCase):
    def setUp(self):
        self.key = generate_data_key()
        self.session_id = "sess-test-001"

    def test_encrypt_decrypt_roundtrip(self):
        payload = {"hello": "world", "n": 42}
        env = encrypt_envelope(self.key, self.session_id, payload, seq=1)
        out = decrypt_envelope(self.key, env)
        self.assertEqual(out, payload)

    def test_replay_seq_rejected(self):
        with self.assertRaises(ValueError):
            validate_replay_state(
                last_seq=5,
                recent_nonces=[],
                seq=5,
                nonce="uuid-1",
                ts=int(time.time() * 1000),
            )

    def test_replay_nonce_rejected(self):
        with self.assertRaises(ValueError):
            validate_replay_state(
                last_seq=1,
                recent_nonces=["uuid-1"],
                seq=2,
                nonce="uuid-1",
                ts=int(time.time() * 1000),
            )

    def test_advance_replay_state(self):
        last, nonces = advance_replay_state(1, ["a"], 2, "b")
        self.assertEqual(last, 2)
        self.assertIn("b", nonces)
