"""Resolve tenant sender identity for outbound email."""

from __future__ import annotations

from core.email.smtp_client import get_platform_smtp_config
from core.models import TenantEmailSettings


def resolve_sender(tenant_id) -> tuple[str, str, str, bool]:
    """
    Returns (from_email, from_name, reply_to, tenant_configured).
  Fallback to platform SMTP from_email when tenant settings missing.
    """
    try:
        settings_obj = TenantEmailSettings.objects.get(tenant_id=tenant_id)
        reply = settings_obj.reply_to or ''
        return settings_obj.from_email, settings_obj.from_name, reply, True
    except TenantEmailSettings.DoesNotExist:
        cfg = get_platform_smtp_config()
        email = cfg.get('from_email') or cfg.get('user', '') or 'noreply@localhost'
        name = cfg.get('from_name', 'AastraaHR')
        return email, name, '', False
