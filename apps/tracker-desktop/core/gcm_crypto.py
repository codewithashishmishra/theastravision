"""AES-256-GCM — must match server core/gcm_crypto.py wire format."""

import base64
import hashlib
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"AASTG1"
NONCE_SIZE = 12
ALGORITHM = "aes-256-gcm"


def generate_data_key() -> bytes:
    return os.urandom(32)


def data_key_from_b64(value: str) -> bytes:
    key = base64.b64decode(value)
    if len(key) != 32:
        raise ValueError("Invalid encryption key length")
    return key


def encrypt_blob(data_key: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(data_key).encrypt(nonce, plaintext, associated_data)
    return MAGIC + nonce + ct


def decrypt_blob(data_key: bytes, blob: bytes, associated_data: bytes) -> bytes:
    if not blob.startswith(MAGIC):
        raise ValueError("Invalid encrypted payload")
    nonce = blob[len(MAGIC) : len(MAGIC) + NONCE_SIZE]
    ct = blob[len(MAGIC) + NONCE_SIZE :]
    return AESGCM(data_key).decrypt(nonce, ct, associated_data)


def derive_local_storage_key(refresh_token: str) -> bytes:
    """Key for encrypting keyring / offline DB (machine-bound to refresh token)."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"aastraa-tracker-offline-v1",
        info=b"local-store",
    )
    return hkdf.derive(refresh_token.encode("utf-8"))


def encrypt_local(plaintext: bytes, refresh_token: str, aad: bytes = b"local") -> bytes:
    return encrypt_blob(derive_local_storage_key(refresh_token), plaintext, aad)


def decrypt_local(blob: bytes, refresh_token: str, aad: bytes = b"local") -> bytes:
    return decrypt_blob(derive_local_storage_key(refresh_token), blob, aad)


def screenshot_aad(session_id: str, checksum: str, monitor: int) -> bytes:
    return f"screenshot:{session_id}:{checksum}:m{monitor}".encode("utf-8")
