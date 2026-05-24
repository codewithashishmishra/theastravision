"""PostgreSQL REDIS session store tests."""

from django.test import TestCase, override_settings

from core.e2ee.session_data import E2EESessionData
from core.e2ee.session_store import PostgresSessionStore, get_session_store
from core.gcm_crypto import generate_data_key


@override_settings(REDIS_ALLOW=False, E2EE_ENABLED=True)
class E2EESessionStoreTests(TestCase):
    def test_postgres_store_round_trip(self):
        store = PostgresSessionStore()
        aes = generate_data_key()
        data = E2EESessionData.create_with_key(aes, client_type="public")
        store.set("test-session-xyz", data, ttl_seconds=3600)
        loaded = store.get("test-session-xyz")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.unwrap_aes_key(), aes)

    def test_factory_uses_postgres_when_redis_disabled(self):
        store = get_session_store()
        self.assertIsInstance(store, PostgresSessionStore)
