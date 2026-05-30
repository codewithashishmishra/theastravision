"""Platform SMTP/IMAP connectivity (EnvConfiguration modules)."""

from __future__ import annotations

import imaplib
import smtplib
import ssl
import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.smtp import EmailBackend
from django.utils.functional import cached_property

from core.models import EnvConfiguration
from core.platform_email_env import build_imap_config_from_env, build_smtp_config_from_env

TRACKING_GIF_BYTES = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00'
    b',\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)

_DETAIL_MAX_LEN = 300


def build_ssl_context(verify: bool = True) -> ssl.SSLContext:
    if verify:
        return ssl.create_default_context()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _config_ssl_verify(cfg: dict) -> bool:
    if getattr(settings, 'PLATFORM_INSECURE_SSL', False):
        return False
    return bool(cfg.get('ssl_verify', True))


def _error_detail(exc: BaseException, max_len: int = _DETAIL_MAX_LEN) -> str:
    msg = str(exc).strip() or exc.__class__.__name__
    if len(msg) > max_len:
        return msg[: max_len - 3] + '...'
    return msg


class PlatformSmtpBackend(EmailBackend):
    """SMTP backend with configurable TLS certificate verification."""

    def __init__(self, *, ssl_verify: bool = True, **kwargs):
        self._ssl_verify = ssl_verify
        super().__init__(**kwargs)

    @cached_property
    def ssl_context(self):
        return build_ssl_context(self._ssl_verify)


def _smtp_config_usable(cfg: dict) -> bool:
    if not cfg.get('host'):
        return False
    if cfg.get('user') and not cfg.get('password'):
        return False
    return True


def _imap_config_usable(cfg: dict) -> bool:
    if not cfg.get('host'):
        return False
    if cfg.get('user') and not cfg.get('password'):
        return False
    return True


def _merge_db_with_env(db_cfg: dict, env_cfg: dict) -> dict:
    """Prefer DB row; fill missing host/user/password from .env fallbacks."""
    merged = {**env_cfg, **{k: v for k, v in db_cfg.items() if v not in (None, '')}}
    if merged.get('user') and not merged.get('password'):
        if env_cfg.get('password'):
            merged['password'] = env_cfg['password']
    return merged


def get_platform_smtp_config() -> dict:
    db_cfg = dict(EnvConfiguration.get_cached_config('SMTP') or {})
    env_cfg = build_smtp_config_from_env()
    merged = _merge_db_with_env(db_cfg, env_cfg)
    if _smtp_config_usable(merged):
        return merged
    if _smtp_config_usable(env_cfg):
        return env_cfg
    return merged


def get_platform_imap_config() -> dict:
    db_cfg = dict(EnvConfiguration.get_cached_config('IMAP') or {})
    env_cfg = build_imap_config_from_env()
    merged = _merge_db_with_env(db_cfg, env_cfg)
    if _imap_config_usable(merged):
        return merged
    if _imap_config_usable(env_cfg):
        return env_cfg
    return merged


def connect_imap(cfg: dict | None = None) -> imaplib.IMAP4:
    """Open an IMAP connection using platform config (caller must login)."""
    cfg = cfg or get_platform_imap_config()
    host = cfg.get('host', '')
    if not host:
        raise ValueError('IMAP host is not configured.')
    port = int(cfg.get('port', 993))
    use_ssl = bool(cfg.get('use_ssl', True))
    ssl_verify = _config_ssl_verify(cfg)
    if use_ssl:
        return imaplib.IMAP4_SSL(host, port, ssl_context=build_ssl_context(ssl_verify))
    return imaplib.IMAP4(host, port)


def build_smtp_connection():
    cfg = get_platform_smtp_config()
    host = cfg.get('host', '')
    if not host:
        raise ValueError('SMTP is not configured. Save SMTP settings under Platform Config.')
    port = int(cfg.get('port', 587))
    use_tls = bool(cfg.get('use_tls', True))
    use_ssl = bool(cfg.get('use_ssl', False))
    user = cfg.get('user', '')
    password = cfg.get('password', '')
    ssl_verify = _config_ssl_verify(cfg)
    return get_connection(
        backend='core.email.smtp_client.PlatformSmtpBackend',
        host=host,
        port=port,
        username=user or None,
        password=password or None,
        use_tls=use_tls,
        use_ssl=use_ssl,
        ssl_verify=ssl_verify,
        fail_silently=False,
    )


def test_smtp_connection(to_email: str, *, from_email: str | None = None, from_name: str | None = None) -> dict:
    start = time.perf_counter()
    cfg = get_platform_smtp_config()
    if not cfg.get('host'):
        return {'ok': False, 'detail': 'SMTP host is not configured.', 'latency_ms': 0}
    if not cfg.get('password') and cfg.get('user'):
        return {
            'ok': False,
            'detail': 'SMTP password is empty. Set PLATFORM_SMTP_PASSWORD in .env and run seed_env_config.',
            'latency_ms': 0,
        }
    sender_email = from_email or cfg.get('from_email') or cfg.get('user', '')
    sender_name = from_name or cfg.get('from_name', 'AastraaHR')
    if not sender_email:
        return {'ok': False, 'detail': 'From email is not configured.', 'latency_ms': 0}
    try:
        conn = build_smtp_connection()
        msg = EmailMultiAlternatives(
            subject='AastraaHR SMTP test',
            body='This is a test message from AastraaHR platform configuration.',
            from_email=f'{sender_name} <{sender_email}>',
            to=[to_email],
            connection=conn,
        )
        msg.attach_alternative(
            '<p>This is a <strong>test email</strong> from AastraaHR SMTP configuration.</p>',
            'text/html',
        )
        msg.send()
    except ssl.SSLCertVerificationError as exc:
        return {
            'ok': False,
            'detail': (
                f'TLS certificate verification failed: {_error_detail(exc)}. '
                'Confirm cPanel host/port (p3plzcpnl506724.prod.phx3.secureserver.net:465 + SSL), or disable '
                '"Verify TLS certificate" if antivirus is intercepting SMTP traffic.'
            ),
            'latency_ms': 0,
        }
    except (smtplib.SMTPException, OSError, ValueError) as exc:
        return {'ok': False, 'detail': _error_detail(exc), 'latency_ms': 0}
    latency = int((time.perf_counter() - start) * 1000)
    return {'ok': True, 'detail': f'Test email sent to {to_email}.', 'latency_ms': latency}


def test_imap_connection() -> dict:
    start = time.perf_counter()
    cfg = get_platform_imap_config()
    host = cfg.get('host', '')
    if not host:
        return {'ok': False, 'detail': 'IMAP host is not configured.', 'mailbox_count': 0}
    if not cfg.get('password') and cfg.get('user'):
        return {
            'ok': False,
            'detail': (
                'IMAP password is empty. Set PLATFORM_IMAP_PASSWORD or PLATFORM_SMTP_PASSWORD '
                'in .env and run seed_env_config.'
            ),
            'mailbox_count': 0,
        }
    port = int(cfg.get('port', 993))
    user = cfg.get('user', '')
    password = cfg.get('password', '')
    folder = cfg.get('folder', 'INBOX')
    try:
        conn = connect_imap(cfg)
        conn.login(user, password)
        status, data = conn.select(folder)
        if status != 'OK':
            conn.logout()
            return {'ok': False, 'detail': f'Could not select folder {folder}.', 'mailbox_count': 0}
        count = int(data[0]) if data and data[0] else 0
        conn.logout()
    except ssl.SSLCertVerificationError as exc:
        return {
            'ok': False,
            'detail': (
                f'TLS certificate verification failed: {_error_detail(exc)}. '
                'Confirm cPanel host/port (p3plzcpnl506724.prod.phx3.secureserver.net:993 + SSL), or disable '
                '"Verify TLS certificate" if antivirus is intercepting IMAP traffic.'
            ),
            'mailbox_count': 0,
        }
    except imaplib.IMAP4.error as exc:
        return {
            'ok': False,
            'detail': (
                f'IMAP error: {_error_detail(exc)}. '
                'Check username (full email), password, and that IMAP is enabled for the mailbox.'
            ),
            'mailbox_count': 0,
        }
    except (OSError, ValueError) as exc:
        return {'ok': False, 'detail': _error_detail(exc), 'mailbox_count': 0}
    latency = int((time.perf_counter() - start) * 1000)
    return {
        'ok': True,
        'detail': f'Connected to {host}, folder {folder}.',
        'mailbox_count': count,
        'latency_ms': latency,
    }


def get_public_api_base_url() -> str:
    return getattr(settings, 'PUBLIC_API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
