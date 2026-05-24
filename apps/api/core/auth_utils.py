"""Shared auth helpers for login flows."""

from django.conf import settings

from core.models import TOTPDevice, WebAuthnCredential


def user_requires_mfa(user) -> bool:
    if not settings.PRIVILEGED_ROLES_REQUIRE_MFA:
        return False
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.role_mappings.filter(
        role__name__in=settings.PRIVILEGED_MFA_ROLE_NAMES
    ).exists()


def user_has_verified_mfa(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if TOTPDevice.objects.filter(user=user, is_verified=True).exists():
        return True
    return WebAuthnCredential.objects.filter(user=user).exists()


def mfa_setup_required_response():
    from rest_framework.response import Response

    return Response(
        {
            "error": "Multi-factor authentication is required for your role. "
            "Set up TOTP or a passkey before signing in.",
            "requires_mfa_setup": True,
        },
        status=403,
    )
