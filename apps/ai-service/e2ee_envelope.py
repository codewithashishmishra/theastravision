"""AES-256-GCM JSON envelopes — mirrors Django core/e2ee/envelope.py."""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"AASTG1"
NONCE_SIZE = 12


def make_aad(session_id: str, seq: int, nonce: str, ts: int) -> bytes:
    return f"{session_id}:{seq}:{nonce}:{ts}".encode("utf-8")


def encrypt_blob(data_key: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(data_key).encrypt(nonce, plaintext, associated_data)
    return MAGIC + nonce + ct


def encrypt_envelope(aes_key: bytes, session_id: str, plaintext_obj: Any, seq: int) -> dict:
    nonce_uuid = str(uuid.uuid4())
    ts = int(time.time() * 1000)
    plaintext = json.dumps(plaintext_obj, separators=(",", ":"), default=str).encode("utf-8")
    aad = make_aad(session_id, seq, nonce_uuid, ts)
    blob = encrypt_blob(aes_key, plaintext, aad)
    iv = blob[6 : 6 + NONCE_SIZE]
    ct = blob[6 + NONCE_SIZE :]
    return {
        "e2ee": True,
        "alg": "aes-256-gcm",
        "session_id": session_id,
        "iv": base64.b64encode(iv).decode("ascii"),
        "ct": base64.b64encode(ct).decode("ascii"),
        "nonce": nonce_uuid,
        "ts": ts,
        "seq": seq,
    }
