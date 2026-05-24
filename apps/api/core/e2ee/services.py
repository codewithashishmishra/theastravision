"""E2EE session lifecycle: handshake, bind to auth, encrypt responses."""

from __future__ import annotations

import secrets
from datetime import timedelta

from cryptography.hazmat.primitives import serialization
from django.conf import settings

from core.gcm_crypto import wrap_data_key

from .ecdh import ALGORITHM, derive_shared_aes_key, export_public_spki_b64, generate_ephemeral_keypair
from .envelope import advance_replay_state, encrypt_envelope
from .session_data import E2EESessionData
from .session_store import get_session_store


def _new_session_id() -> str:
    return secrets.token_urlsafe(32)


def _serialize_private_key(private_key) -> str:
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("ascii")


def _load_private_key(pem: str):
    return serialization.load_pem_private_key(pem.encode("ascii"), password=None)


def public_session_ttl() -> int:
    return int(getattr(settings, "E2EE_PUBLIC_SESSION_TTL_SECONDS", 900))


def auth_session_ttl() -> int:
    return int(getattr(settings, "E2EE_SESSION_TTL_SECONDS", 604800))


def create_handshake_session(
    client_ecdh_public: str,
    *,
    client_type: str = "public",
    user_id: str | None = None,
    refresh_jti: str | None = None,
) -> dict:
    session_id = _new_session_id()
    private_key, public_key = generate_ephemeral_keypair()
    aes_key = derive_shared_aes_key(private_key, client_ecdh_public, session_id)
    ttl = auth_session_ttl() if user_id else public_session_ttl()
    data = E2EESessionData.create_with_key(
        aes_key,
        client_type=client_type,
        user_id=user_id,
        refresh_jti=refresh_jti,
        server_ecdh_private_pem=_serialize_private_key(private_key),
    )
    get_session_store().set(session_id, data, ttl)
    return {
        "session_id": session_id,
        "server_ecdh_public": export_public_spki_b64(public_key),
        "alg": ALGORITHM,
        "ttl_seconds": ttl,
    }


def bind_session_to_auth(
    session_id: str | None,
    client_ecdh_public: str | None,
    *,
    user_id: str,
    refresh_jti: str,
    client_type: str = "web",
) -> dict | None:
    """Upgrade anonymous session or create authenticated E2EE session on login."""
    if not client_ecdh_public:
        return None
    store = get_session_store()
    if session_id:
        existing = store.get(session_id)
        if existing and existing.server_ecdh_private_pem:
            private_key = _load_private_key(existing.server_ecdh_private_pem)
            aes_key = derive_shared_aes_key(private_key, client_ecdh_public, session_id)
            data = E2EESessionData.create_with_key(
                aes_key,
                client_type=client_type,
                user_id=str(user_id),
                refresh_jti=str(refresh_jti),
                server_ecdh_private_pem=existing.server_ecdh_private_pem,
            )
            store.set(session_id, data, auth_session_ttl())
            return {"e2ee_session_id": session_id, "alg": ALGORITHM}
    handshake = create_handshake_session(
        client_ecdh_public,
        client_type=client_type,
        user_id=str(user_id),
        refresh_jti=str(refresh_jti),
    )
    return {
        "e2ee_session_id": handshake["session_id"],
        "server_ecdh_public": handshake["server_ecdh_public"],
        "alg": handshake["alg"],
    }


def wrap_auth_session_key(aes_key: bytes) -> str:
    return wrap_data_key(aes_key)


def delete_session(session_id: str | None) -> None:
    if session_id:
        get_session_store().delete(session_id)


def delete_sessions_for_refresh_jti(refresh_jti: str) -> None:
    """Best-effort cleanup on logout — scan not needed if session_id passed in header."""
    pass


def load_session_aes_key(session_id: str) -> tuple[bytes, E2EESessionData] | None:
    data = get_session_store().get(session_id)
    if not data:
        return None
    return data.unwrap_aes_key(), data


def encrypt_response_for_session(session_id: str, body_obj, request_seq: int | None = None) -> dict | None:
    loaded = load_session_aes_key(session_id)
    if not loaded:
        return None
    aes_key, data = loaded
    next_seq = (data.last_seq + 1) if request_seq is None else max(data.last_seq + 1, int(request_seq))
    envelope = encrypt_envelope(aes_key, session_id, body_obj, next_seq)
    data.last_seq, data.recent_nonces = advance_replay_state(
        data.last_seq,
        data.recent_nonces,
        next_seq,
        envelope["nonce"],
    )
    ttl = auth_session_ttl() if data.user_id else public_session_ttl()
    get_session_store().touch(session_id, data, ttl)
    return envelope


def get_session_for_internal(session_id: str) -> dict | None:
    data = get_session_store().get(session_id)
    if not data:
        return None
    return {
        "session_id": session_id,
        "client_type": data.client_type,
        "user_id": data.user_id,
        "last_seq": data.last_seq,
    }


def export_session_aes_key_b64(session_id: str) -> str | None:
    loaded = load_session_aes_key(session_id)
    if not loaded:
        return None
    import base64

    aes_key, _ = loaded
    return base64.b64encode(aes_key).decode("ascii")
