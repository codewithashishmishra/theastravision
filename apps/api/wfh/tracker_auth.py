"""Desktop tracker sessions — independent from web browser logout."""

import base64

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from core.gcm_crypto import ALGORITHM, generate_data_key, wrap_data_key
from core.models import AuthSession, User
from wfh.utils import get_client_ip


def _session_meta(request):
    if not request:
        return {}
    return {
        "device_fingerprint": request.META.get("HTTP_USER_AGENT", "tracker-desktop")[:255],
        "ip_address": get_client_ip(request),
        "user_agent": request.META.get("HTTP_USER_AGENT", "AastraaTracker/1.0"),
    }


def _encryption_fields(data_key: bytes) -> dict:
    return {
        "encryption_key": base64.b64encode(data_key).decode("ascii"),
        "encryption_algorithm": ALGORITHM,
    }


def issue_tracker_session(user: User, request=None, login_method: str = "password"):
    """Create a tracker-only refresh session (not revoked by web logout)."""
    refresh = RefreshToken.for_user(user)
    data_key = generate_data_key()
    AuthSession.objects.create(
        user=user,
        refresh_token_jti=refresh["jti"],
        login_method=login_method,
        client_type="tracker",
        payload_key_wrapped=wrap_data_key(data_key),
        **_session_meta(request),
    )
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        **_encryption_fields(data_key),
    }


def exchange_access_for_tracker_session(access_token: str, request=None):
    """Turn a short-lived web access token into a dedicated tracker session."""
    token = AccessToken(access_token)
    user_id = token.get("user_id")
    if not user_id:
        raise ValueError("Invalid access token")
    user = User.objects.filter(pk=user_id).first()
    if not user:
        raise ValueError("User not found")
    return issue_tracker_session(user, request=request)


def refresh_tracker_session(refresh_token: str):
    token = RefreshToken(refresh_token)
    session = AuthSession.objects.filter(
        refresh_token_jti=token["jti"], client_type="tracker", is_revoked=False
    ).first()
    if not session:
        raise ValueError("Tracker session expired or revoked")
    new_refresh = RefreshToken.for_user(session.user)
    session.is_revoked = True
    session.save(update_fields=["is_revoked"])
    data_key = generate_data_key()
    AuthSession.objects.create(
        user=session.user,
        refresh_token_jti=new_refresh["jti"],
        login_method=session.login_method,
        client_type="tracker",
        device_fingerprint=session.device_fingerprint,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        payload_key_wrapped=wrap_data_key(data_key),
    )
    return {
        "access_token": str(new_refresh.access_token),
        "refresh_token": str(new_refresh),
        **_encryption_fields(data_key),
    }


def latest_tracker_key_wrapped(user: User) -> str | None:
    row = (
        AuthSession.objects.filter(
            user=user,
            client_type="tracker",
            is_revoked=False,
            payload_key_wrapped__isnull=False,
        )
        .exclude(payload_key_wrapped="")
        .order_by("-created_at")
        .first()
    )
    return row.payload_key_wrapped if row else None


def revoke_tracker_session(refresh_token: str):
    try:
        token = RefreshToken(refresh_token)
        AuthSession.objects.filter(
            refresh_token_jti=token["jti"], client_type="tracker"
        ).update(is_revoked=True)
    except Exception:
        pass
