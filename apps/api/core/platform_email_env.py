"""Platform SMTP/IMAP defaults from environment (GoDaddy / notifications@ mailbox)."""

from __future__ import annotations

import os

PLATFORM_EMAIL_USER_DEFAULT = 'notifications@theastravision.com'
# cPanel "Secure SSL/TLS" — same host for IMAP (993) and SMTP (465) per mailbox setup.
PLATFORM_CPANEL_MAIL_HOST = 'p3plzcpnl506724.prod.phx3.secureserver.net'


def env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key, '').strip().lower()
    if not raw:
        return default
    return raw in ('true', '1', 'yes')


def platform_smtp_password_from_env() -> str:
    return os.environ.get('PLATFORM_SMTP_PASSWORD', '').strip()


def platform_imap_password_from_env() -> str:
    return (
        os.environ.get('PLATFORM_IMAP_PASSWORD', '').strip()
        or platform_smtp_password_from_env()
    )


def build_smtp_config_from_env() -> dict:
    return {
        'host': os.environ.get('PLATFORM_SMTP_HOST', PLATFORM_CPANEL_MAIL_HOST),
        'port': int(os.environ.get('PLATFORM_SMTP_PORT', '465')),
        'use_tls': env_bool('PLATFORM_SMTP_USE_TLS', False),
        'use_ssl': env_bool('PLATFORM_SMTP_USE_SSL', True),
        'user': os.environ.get('PLATFORM_SMTP_USER', PLATFORM_EMAIL_USER_DEFAULT),
        'password': platform_smtp_password_from_env(),
        'from_email': os.environ.get('PLATFORM_SMTP_FROM_EMAIL', PLATFORM_EMAIL_USER_DEFAULT),
        'from_name': os.environ.get('PLATFORM_SMTP_FROM_NAME', 'The Astra Vision'),
        'rate_per_minute': int(os.environ.get('PLATFORM_SMTP_RATE_PER_MINUTE', '30')),
        'ssl_verify': env_bool('PLATFORM_SMTP_SSL_VERIFY', True),
    }


def build_imap_config_from_env() -> dict:
    return {
        'host': os.environ.get('PLATFORM_IMAP_HOST', PLATFORM_CPANEL_MAIL_HOST),
        'port': int(os.environ.get('PLATFORM_IMAP_PORT', '993')),
        'use_ssl': env_bool('PLATFORM_IMAP_USE_SSL', True),
        'user': os.environ.get('PLATFORM_IMAP_USER', PLATFORM_EMAIL_USER_DEFAULT),
        'password': platform_imap_password_from_env(),
        'folder': os.environ.get('PLATFORM_IMAP_FOLDER', 'INBOX'),
        'poll_interval_minutes': int(os.environ.get('PLATFORM_IMAP_POLL_INTERVAL_MINUTES', '5')),
        'ssl_verify': env_bool('PLATFORM_IMAP_SSL_VERIFY', True),
    }


def imap_mailbox_key_from_config(cfg: dict) -> str:
    """Stable key per IMAP account so UID cursors never mix across mailboxes."""
    user = (cfg.get('user') or '').strip().lower()
    host = (cfg.get('host') or '').strip().lower()
    folder = (cfg.get('folder') or 'INBOX').strip()
    if not user or not host:
        return 'default'
    return f'{user}@{host}:{folder}'
