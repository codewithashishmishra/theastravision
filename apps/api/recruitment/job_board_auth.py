"""API key authentication for the public job board."""

from __future__ import annotations

import hashlib
import secrets

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from core.addons import tenant_has_addon
from core.models import TenantAddon
from recruitment.models import TenantCareerPortalSettings


def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, prefix, hash)."""
    raw = secrets.token_urlsafe(32)
    prefix = f'jb_live_{raw[:8]}'
    full_key = f'{prefix}_{secrets.token_urlsafe(24)}'
    key_hash = hash_api_key(full_key)
    return full_key, prefix, key_hash


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode('utf-8')).hexdigest()


def verify_api_key(key: str, settings: TenantCareerPortalSettings) -> bool:
    return secrets.compare_digest(hash_api_key(key), settings.api_key_hash)


class JobBoardApiKeyAuthentication(BaseAuthentication):
    """Authenticate via X-Job-Board-Key header or ?key= query param."""

    def authenticate(self, request):
        key = (
            request.headers.get('X-Job-Board-Key')
            or request.META.get('HTTP_X_JOB_BOARD_KEY')
            or request.query_params.get('key')
        )
        if not key:
            raise AuthenticationFailed('Job board API key required.')
        key_hash = hash_api_key(key)
        try:
            settings = TenantCareerPortalSettings.objects.select_related('tenant').get(
                api_key_hash=key_hash
            )
        except TenantCareerPortalSettings.DoesNotExist:
            raise AuthenticationFailed('Invalid job board API key.') from None
        if not tenant_has_addon(settings.tenant_id, TenantAddon.ADDON_JOB_PORTAL):
            raise PermissionDenied('Job Portal add-on is not enabled for this organization.')
        request.job_board_settings = settings
        request.job_board_tenant = settings.tenant
        request.tenant_id = settings.tenant_id
        return (None, settings)
