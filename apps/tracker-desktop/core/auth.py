"""Secure token storage — desktop session lasts up to 7 days."""

import json
from datetime import datetime, timedelta, timezone

import keyring

SERVICE = "aastraa_tracker"
SESSION_DAYS = 7


def save_session(email: str, access_token: str, refresh_token: str, encryption_key_b64: str | None = None):
    keyring.set_password(SERVICE, f"{email}:access", access_token)
    keyring.set_password(SERVICE, f"{email}:refresh", refresh_token)
    keyring.set_password(SERVICE, "active_email", email)
    if encryption_key_b64:
        keyring.set_password(SERVICE, f"{email}:enc_key", encryption_key_b64)
    meta = {
        "email": email,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "expires_days": SESSION_DAYS,
    }
    keyring.set_password(SERVICE, "session_meta", json.dumps(meta))


def load_session():
    """Return session dict if valid within SESSION_DAYS, else None."""
    email = keyring.get_password(SERVICE, "active_email")
    if not email:
        return None
    meta_raw = keyring.get_password(SERVICE, "session_meta")
    if meta_raw:
        try:
            meta = json.loads(meta_raw)
            saved_at = datetime.fromisoformat(meta["saved_at"])
            if saved_at.tzinfo is None:
                saved_at = saved_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - saved_at > timedelta(days=SESSION_DAYS):
                clear_session()
                return None
        except Exception:
            pass
    access = keyring.get_password(SERVICE, f"{email}:access")
    refresh = keyring.get_password(SERVICE, f"{email}:refresh")
    enc_key = keyring.get_password(SERVICE, f"{email}:enc_key")
    if not access or not refresh:
        return None
    out = {"email": email, "access_token": access, "refresh_token": refresh}
    if enc_key:
        out["encryption_key"] = enc_key
    return out


def clear_session():
    email = keyring.get_password(SERVICE, "active_email")
    if email:
        for suffix in ("access", "refresh", "enc_key"):
            try:
                keyring.delete_password(SERVICE, f"{email}:{suffix}")
            except Exception:
                pass
    for key in ("active_email", "session_meta"):
        try:
            keyring.delete_password(SERVICE, key)
        except Exception:
            pass


def save_tokens(email: str, access_token: str, refresh_token: str = "", encryption_key_b64: str | None = None):
    if refresh_token:
        save_session(email, access_token, refresh_token, encryption_key_b64)
    else:
        keyring.set_password(SERVICE, f"{email}:access", access_token)
