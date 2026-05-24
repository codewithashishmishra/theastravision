import hashlib

from core.gcm_crypto import ALGORITHM, decrypt_blob, encrypt_blob

__all__ = ["encrypt_bytes", "decrypt_bytes", "sha256", "ALGORITHM"]


def encrypt_bytes(data: bytes, data_key: bytes, aad: bytes) -> bytes:
    return encrypt_blob(data_key, data, aad)


def decrypt_bytes(blob: bytes, data_key: bytes, aad: bytes) -> bytes:
    return decrypt_blob(data_key, blob, aad)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
