from __future__ import annotations

import base64
import json
import threading
from dataclasses import dataclass

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


HKDF_INFO = b"aastraa-e2ee-v1"


@dataclass
class _SessionState:
    session_id: str = ""
    aes_key: bytes | None = None
    seq: int = 0


class E2EEClient:
    def __init__(self, api_base: str):
        self.api_base = api_base.rstrip("/")
        self._state = _SessionState()
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._state = _SessionState()

    def ensure_session(self):
        with self._lock:
            if self._state.session_id and self._state.aes_key:
                return
            private_key = ec.generate_private_key(ec.SECP256R1())
            public_key = private_key.public_key()
            client_pub_der = public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            res = httpx.post(
                f"{self.api_base}/public/e2ee/handshake/",
                json={
                    "client_ecdh_public": base64.b64encode(client_pub_der).decode("ascii"),
                    "client_type": "tracker",
                },
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=30.0,
            )
            res.raise_for_status()
            body = res.json()
            session_id = body["session_id"]
            server_pub_der = base64.b64decode(body["server_ecdh_public"])
            server_pub = serialization.load_der_public_key(server_pub_der)
            shared = private_key.exchange(ec.ECDH(), server_pub)
            aes_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=session_id.encode("utf-8"),
                info=HKDF_INFO,
            ).derive(shared)
            self._state.session_id = session_id
            self._state.aes_key = aes_key
            self._state.seq = 0

    def auth_headers(self) -> dict[str, str]:
        with self._lock:
            if not self._state.session_id:
                return {}
            self._state.seq += 1
            return {
                "X-E2EE-Session": self._state.session_id,
                "X-E2EE-Seq": str(self._state.seq),
            }

    def decrypt_if_needed(self, payload):
        if not isinstance(payload, dict) or payload.get("e2ee") is not True:
            return payload
        with self._lock:
            key = self._state.aes_key
        if not key:
            raise ValueError("Missing E2EE AES key for envelope decryption.")
        session_id = payload["session_id"]
        seq = int(payload["seq"])
        nonce = payload["nonce"]
        ts = int(payload["ts"])
        aad = f"{session_id}:{seq}:{nonce}:{ts}".encode("utf-8")
        iv = base64.b64decode(payload["iv"])
        ct = base64.b64decode(payload["ct"])
        blob = b"AASTG1" + iv + ct
        from core.gcm_crypto import decrypt_blob

        plaintext = decrypt_blob(key, blob, aad)
        return json.loads(plaintext.decode("utf-8"))

