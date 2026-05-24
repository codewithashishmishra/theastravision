"""AES-256-GCM JSON response envelopes with replay metadata."""

from __future__ import annotations

import base64
import json
import time
import uuid
from typing import Any

from core.gcm_crypto import NONCE_SIZE, decrypt_blob, encrypt_blob

REPLAY_WINDOW_MS = 5 * 60 * 1000
MAX_RECENT_NONCES = 64


def make_aad(session_id: str, seq: int, nonce: str, ts: int) -> bytes:
    return f"{session_id}:{seq}:{nonce}:{ts}".encode("utf-8")


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


def decrypt_envelope(aes_key: bytes, envelope: dict) -> Any:
    session_id = envelope["session_id"]
    seq = int(envelope["seq"])
    nonce = envelope["nonce"]
    ts = int(envelope["ts"])
    iv = base64.b64decode(envelope["iv"])
    ct = base64.b64decode(envelope["ct"])
    blob = b"AASTG1" + iv + ct
    aad = make_aad(session_id, seq, nonce, ts)
    plaintext = decrypt_blob(aes_key, blob, aad)
    return json.loads(plaintext.decode("utf-8"))


def validate_replay_state(
    *,
    last_seq: int,
    recent_nonces: list[str],
    seq: int,
    nonce: str,
    ts: int,
) -> None:
    now_ms = int(time.time() * 1000)
    if abs(now_ms - ts) > REPLAY_WINDOW_MS:
        raise ValueError("Envelope timestamp outside replay window")
    if seq <= last_seq:
        raise ValueError("Envelope sequence replay detected")
    if nonce in recent_nonces:
        raise ValueError("Envelope nonce reused")


def advance_replay_state(last_seq: int, recent_nonces: list[str], seq: int, nonce: str) -> tuple[int, list[str]]:
    nonces = list(recent_nonces)
    nonces.append(nonce)
    if len(nonces) > MAX_RECENT_NONCES:
        nonces = nonces[-MAX_RECENT_NONCES:]
    return max(last_seq, seq), nonces
