"""ECDH P-256 key exchange and HKDF session key derivation."""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey, EllipticCurvePublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

CURVE = ec.SECP256R1()
HKDF_INFO = b"aastraa-e2ee-v1"
ALGORITHM = "aes-256-gcm"


def generate_ephemeral_keypair() -> tuple[EllipticCurvePrivateKey, EllipticCurvePublicKey]:
    private_key = ec.generate_private_key(CURVE)
    return private_key, private_key.public_key()


def export_public_spki_b64(public_key: EllipticCurvePublicKey) -> str:
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(der).decode("ascii")


def load_public_spki_b64(value: str) -> EllipticCurvePublicKey:
    der = base64.b64decode(value)
    key = serialization.load_der_public_key(der)
    if not isinstance(key, EllipticCurvePublicKey):
        raise ValueError("Expected ECDH public key")
    return key


def derive_shared_aes_key(
    private_key: EllipticCurvePrivateKey,
    peer_public_b64: str,
    session_id: str,
) -> bytes:
    peer_public = load_public_spki_b64(peer_public_b64)
    shared = private_key.exchange(ec.ECDH(), peer_public)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=session_id.encode("utf-8"),
        info=HKDF_INFO,
    )
    return hkdf.derive(shared)
