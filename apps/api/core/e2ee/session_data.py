"""In-memory representation of an E2EE session."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from core.gcm_crypto import unwrap_data_key, wrap_data_key


@dataclass
class E2EESessionData:
    wrapped_key: str
    last_seq: int = 0
    recent_nonces: list[str] = field(default_factory=list)
    user_id: str | None = None
    refresh_jti: str | None = None
    client_type: str = "public"
    server_ecdh_private_pem: str | None = None

    def to_json_bytes(self) -> bytes:
        return json.dumps(asdict(self), separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_json_bytes(cls, raw: bytes) -> E2EESessionData:
        data = json.loads(raw.decode("utf-8"))
        return cls(
            wrapped_key=data["wrapped_key"],
            last_seq=int(data.get("last_seq", 0)),
            recent_nonces=list(data.get("recent_nonces") or []),
            user_id=data.get("user_id"),
            refresh_jti=data.get("refresh_jti"),
            client_type=data.get("client_type") or "public",
            server_ecdh_private_pem=data.get("server_ecdh_private_pem"),
        )

    def unwrap_aes_key(self) -> bytes:
        return unwrap_data_key(self.wrapped_key)

    @classmethod
    def create_with_key(
        cls,
        aes_key: bytes,
        *,
        client_type: str = "public",
        user_id: str | None = None,
        refresh_jti: str | None = None,
        server_ecdh_private_pem: str | None = None,
    ) -> E2EESessionData:
        return cls(
            wrapped_key=wrap_data_key(aes_key),
            client_type=client_type,
            user_id=user_id,
            refresh_jti=refresh_jti,
            server_ecdh_private_pem=server_ecdh_private_pem,
        )


def expires_at_from_ttl(seconds: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)
