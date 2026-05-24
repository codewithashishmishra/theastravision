"""ECDH key derivation symmetry tests."""

from django.test import SimpleTestCase

from core.e2ee.ecdh import (
    derive_shared_aes_key,
    export_public_spki_b64,
    generate_ephemeral_keypair,
    load_public_spki_b64,
)


class E2EECdhTests(SimpleTestCase):
    def test_client_server_derive_same_aes_key(self):
        session_id = "test-session-abc123"
        client_priv, client_pub = generate_ephemeral_keypair()
        server_priv, server_pub = generate_ephemeral_keypair()

        client_pub_b64 = export_public_spki_b64(client_pub)
        server_pub_b64 = export_public_spki_b64(server_pub)

        client_key = derive_shared_aes_key(client_priv, server_pub_b64, session_id)
        server_key = derive_shared_aes_key(server_priv, client_pub_b64, session_id)

        self.assertEqual(client_key, server_key)
        self.assertEqual(len(client_key), 32)

    def test_load_public_spki_roundtrip(self):
        _, pub = generate_ephemeral_keypair()
        b64 = export_public_spki_b64(pub)
        loaded = load_public_spki_b64(b64)
        self.assertEqual(export_public_spki_b64(loaded), b64)
