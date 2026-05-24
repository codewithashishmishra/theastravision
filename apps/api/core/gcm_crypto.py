"""
AES-256-GCM for tracker payloads at rest and in transit (application layer).

Wire format: MAGIC (6) || nonce (12) || ciphertext+tag
"""

import base64
import hashlib
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings

MAGIC = b"AASTG1"
NONCE_SIZE = 12
ALGORITHM = "aes-256-gcm"


def _master_key() -> bytes:
    raw = getattr(settings, "TRACKER_MASTER_KEY", None) or settings.SECRET_KEY
    if isinstance(raw, str):
        raw = raw.encode()
    return hashlib.sha256(raw).digest()


def generate_data_key() -> bytes:
    return os.urandom(32)


def wrap_data_key(data_key: bytes) -> str:
    """Wrap session data key with server master key for DB storage."""
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(_master_key()).encrypt(nonce, data_key, b"aastraa-wrap-key-v1")
    return base64.b64encode(MAGIC + nonce + ct).decode("ascii")


def unwrap_data_key(wrapped_b64: str) -> bytes:
    blob = base64.b64decode(wrapped_b64)
    _assert_magic(blob)
    nonce = blob[len(MAGIC) : len(MAGIC) + NONCE_SIZE]
    ct = blob[len(MAGIC) + NONCE_SIZE :]
    return AESGCM(_master_key()).decrypt(nonce, ct, b"aastraa-wrap-key-v1")


def encrypt_blob(data_key: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(data_key).encrypt(nonce, plaintext, associated_data)
    return MAGIC + nonce + ct


def decrypt_blob(data_key: bytes, blob: bytes, associated_data: bytes) -> bytes:
    _assert_magic(blob)
    nonce = blob[len(MAGIC) : len(MAGIC) + NONCE_SIZE]
    ct = blob[len(MAGIC) + NONCE_SIZE :]
    return AESGCM(data_key).decrypt(nonce, ct, associated_data)


def wrap_blob_at_rest(plaintext: bytes, aad: bytes) -> bytes:
    """Second layer: encrypt for filesystem/DB using server master key."""
    return encrypt_blob(_master_key(), plaintext, aad)


def unwrap_blob_at_rest(blob: bytes, aad: bytes) -> bytes:
    return decrypt_blob(_master_key(), blob, aad)


def is_gcm_blob(data: bytes) -> bool:
    return len(data) > len(MAGIC) + NONCE_SIZE + 16 and data.startswith(MAGIC)


def _assert_magic(blob: bytes) -> None:
    if not is_gcm_blob(blob):
        raise ValueError("Invalid encrypted payload (bad magic)")


def screenshot_aad(session_id, checksum: str, monitor: int) -> bytes:
    return f"screenshot:{session_id}:{checksum}:m{monitor}".encode("utf-8")
