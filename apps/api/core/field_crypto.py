"""Encrypt sensitive PII fields (SSN, SIN) at rest."""

from __future__ import annotations

import base64

from core.gcm_crypto import unwrap_blob_at_rest, wrap_blob_at_rest


def encrypt_sensitive(value: str, field_name: str) -> str:
    if not value:
        return ''
    blob = wrap_blob_at_rest(value.encode('utf-8'), f'sensitive:{field_name}'.encode('utf-8'))
    return base64.b64encode(blob).decode('ascii')


def decrypt_sensitive(stored: str, field_name: str) -> str:
    if not stored:
        return ''
    try:
        blob = base64.b64decode(stored)
        plain = unwrap_blob_at_rest(blob, f'sensitive:{field_name}'.encode('utf-8'))
        return plain.decode('utf-8')
    except Exception:
        return ''


def mask_sensitive(value: str, visible_tail: int = 4) -> str:
    if not value or len(value) <= visible_tail:
        return '****'
    return '*' * (len(value) - visible_tail) + value[-visible_tail:]
