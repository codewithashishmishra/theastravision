"""
Generate development secrets and optionally write apps/api/.env + apps/ai-service/.env.

Run: python manage.py generate_dev_secrets --write
After rotating crypto keys: python manage.py reset_env_encryption
"""

from __future__ import annotations

import secrets
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

# Keys whose values are always regenerated
GENERATED_KEYS = {
    "SECRET_KEY": 64,
    "TRACKER_MASTER_KEY": 48,
    "TRACKER_ENCRYPTION_KEY": 48,
    "E2EE_INTERNAL_TOKEN": 32,
}

# Preserved from existing .env when present (never auto-generated)
PRESERVE_KEYS = frozenset(
    {
        "DATABASE_URL",
        "REDIS_URL",
        "PLATFORM_INSECURE_SSL",
        "DISABLE_SSL_VERIFY",
        "PLATFORM_SMTP_HOST",
        "PLATFORM_SMTP_PORT",
        "PLATFORM_SMTP_USE_TLS",
        "PLATFORM_SMTP_USE_SSL",
        "PLATFORM_SMTP_USER",
        "PLATFORM_SMTP_PASSWORD",
        "PLATFORM_SMTP_FROM_EMAIL",
        "PLATFORM_SMTP_FROM_NAME",
        "PLATFORM_SMTP_SSL_VERIFY",
        "PLATFORM_IMAP_HOST",
        "PLATFORM_IMAP_PORT",
        "PLATFORM_IMAP_USE_SSL",
        "PLATFORM_IMAP_USER",
        "PLATFORM_IMAP_PASSWORD",
        "PLATFORM_DEFAULT_TENANT_FROM_EMAIL",
        "PLATFORM_SMTP_RATE_PER_MINUTE",
        "PLATFORM_IMAP_FOLDER",
        "PLATFORM_IMAP_POLL_INTERVAL_MINUTES",
        "PLATFORM_IMAP_SSL_VERIFY",
        "PLATFORM_OPENAI_API_KEY",
        "PLATFORM_OPENAI_MODEL",
    }
)

API_ENV_TEMPLATE_KEYS = [
    "DEBUG",
    "SECRET_KEY",
    "",
    "DATABASE_URL",
    "REDIS_URL",
    "",
    "ALLOW_S3",
    "AI_SERVICE_BASE_URL",
    "FRONTEND_APP_URL",
    "CAREERS_APP_URL",
    "PUBLIC_API_BASE_URL",
    "",
    "REDIS_ALLOW",
    "E2EE_ENABLED",
    "E2EE_INTERNAL_TOKEN",
    "E2EE_SESSION_TTL_SECONDS",
    "E2EE_PUBLIC_SESSION_TTL_SECONDS",
    "",
    "METRICS_ENABLED",
    "METRICS_RETENTION_HOURS",
    "",
    "CLICKHOUSE_ENABLED",
    "CLICKHOUSE_HOST",
    "CLICKHOUSE_PORT",
    "CLICKHOUSE_USER",
    "CLICKHOUSE_PASSWORD",
    "CLICKHOUSE_DATABASE",
    "",
    "TRACKER_MASTER_KEY",
    "TRACKER_ENCRYPTION_KEY",
    "WFH_TRACKING_ENABLED",
    "",
    "JWT_ACCESS_MINUTES",
    "JWT_REFRESH_DAYS",
    "",
    "UTIL_COOLDOWN_CPU_THRESHOLD",
    "UTIL_COOLDOWN_RAM_THRESHOLD",
    "UTIL_COOLDOWN_DURATION_SECONDS",
    "UTIL_SAMPLE_INTERVAL_SECONDS",
    "UTIL_COOLDOWN_SUPER_ADMIN_BYPASS",
    "",
    "WEBAUTHN_RP_ID",
    "WEBAUTHN_RP_NAME",
    "WEBAUTHN_ORIGIN",
    "",
    "PLATFORM_INSECURE_SSL",
    "",
    "PLATFORM_SMTP_HOST",
    "PLATFORM_SMTP_PORT",
    "PLATFORM_SMTP_USE_TLS",
    "PLATFORM_SMTP_USE_SSL",
    "PLATFORM_SMTP_USER",
    "PLATFORM_SMTP_PASSWORD",
    "PLATFORM_SMTP_FROM_EMAIL",
    "PLATFORM_SMTP_FROM_NAME",
    "PLATFORM_SMTP_SSL_VERIFY",
    "PLATFORM_IMAP_HOST",
    "PLATFORM_IMAP_PORT",
    "PLATFORM_IMAP_USE_SSL",
    "PLATFORM_IMAP_USER",
    "PLATFORM_IMAP_PASSWORD",
    "PLATFORM_DEFAULT_TENANT_FROM_EMAIL",
    "PLATFORM_SMTP_RATE_PER_MINUTE",
    "PLATFORM_IMAP_FOLDER",
    "PLATFORM_IMAP_POLL_INTERVAL_MINUTES",
    "PLATFORM_IMAP_SSL_VERIFY",
    "",
    "PLATFORM_OPENAI_API_KEY",
    "PLATFORM_OPENAI_MODEL",
]

DEFAULTS = {
    "DEBUG": "True",
    "DATABASE_URL": "postgres://postgres:password@localhost:5432/aastraahr_db",
    "REDIS_URL": "redis://localhost:6379/0",
    "ALLOW_S3": "False",
    "AI_SERVICE_BASE_URL": "http://127.0.0.1:8001",
    "FRONTEND_APP_URL": "http://localhost:3000",
    "CAREERS_APP_URL": "http://localhost:3001",
    "PUBLIC_API_BASE_URL": "http://127.0.0.1:8000",
    "REDIS_ALLOW": "True",
    "E2EE_ENABLED": "True",
    "E2EE_SESSION_TTL_SECONDS": "604800",
    "E2EE_PUBLIC_SESSION_TTL_SECONDS": "900",
    "METRICS_ENABLED": "True",
    "METRICS_RETENTION_HOURS": "72",
    "CLICKHOUSE_ENABLED": "False",
    "CLICKHOUSE_HOST": "localhost",
    "CLICKHOUSE_PORT": "8123",
    "CLICKHOUSE_USER": "default",
    "CLICKHOUSE_PASSWORD": "",
    "CLICKHOUSE_DATABASE": "default",
    "WFH_TRACKING_ENABLED": "True",
    "JWT_ACCESS_MINUTES": "15",
    "JWT_REFRESH_DAYS": "7",
    "UTIL_COOLDOWN_CPU_THRESHOLD": "80",
    "UTIL_COOLDOWN_RAM_THRESHOLD": "80",
    "UTIL_COOLDOWN_DURATION_SECONDS": "300",
    "UTIL_SAMPLE_INTERVAL_SECONDS": "30",
    "UTIL_COOLDOWN_SUPER_ADMIN_BYPASS": "false",
    "WEBAUTHN_RP_ID": "localhost",
    "WEBAUTHN_RP_NAME": "AastraaHR",
    "WEBAUTHN_ORIGIN": "http://localhost:3000",
    "PLATFORM_INSECURE_SSL": "false",
    "PLATFORM_SMTP_HOST": "p3plzcpnl506724.prod.phx3.secureserver.net",
    "PLATFORM_SMTP_PORT": "465",
    "PLATFORM_SMTP_USE_TLS": "false",
    "PLATFORM_SMTP_USE_SSL": "true",
    "PLATFORM_SMTP_USER": "notifications@theastravision.com",
    "PLATFORM_SMTP_PASSWORD": "",
    "PLATFORM_SMTP_FROM_EMAIL": "notifications@theastravision.com",
    "PLATFORM_SMTP_FROM_NAME": "The Astra Vision",
    "PLATFORM_SMTP_SSL_VERIFY": "true",
    "PLATFORM_IMAP_HOST": "p3plzcpnl506724.prod.phx3.secureserver.net",
    "PLATFORM_IMAP_PORT": "993",
    "PLATFORM_IMAP_USE_SSL": "true",
    "PLATFORM_IMAP_USER": "notifications@theastravision.com",
    "PLATFORM_IMAP_PASSWORD": "",
    "PLATFORM_DEFAULT_TENANT_FROM_EMAIL": "notifications@theastravision.com",
    "PLATFORM_SMTP_RATE_PER_MINUTE": "30",
    "PLATFORM_IMAP_FOLDER": "INBOX",
    "PLATFORM_IMAP_POLL_INTERVAL_MINUTES": "5",
    "PLATFORM_IMAP_SSL_VERIFY": "true",
    "PLATFORM_OPENAI_API_KEY": "",
    "PLATFORM_OPENAI_MODEL": "gpt-5.4-mini",
}


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()
    return result


def _token(nbytes: int) -> str:
    return secrets.token_urlsafe(nbytes)


def _build_env_values(
    existing: dict[str, str],
    *,
    force_email: bool,
    ai_env: dict[str, str] | None = None,
) -> dict[str, str]:
    values = dict(DEFAULTS)
    for key in PRESERVE_KEYS:
        if key in existing and existing[key]:
            values[key] = existing[key]
    if not force_email:
        for key in ("PLATFORM_SMTP_PASSWORD", "PLATFORM_IMAP_PASSWORD"):
            if key in existing and existing[key]:
                values[key] = existing[key]
    ai_env = ai_env or {}
    if not values.get("PLATFORM_OPENAI_API_KEY") and ai_env.get("OPENAI_API_KEY"):
        values["PLATFORM_OPENAI_API_KEY"] = ai_env["OPENAI_API_KEY"]
    if not values.get("PLATFORM_OPENAI_MODEL") or values["PLATFORM_OPENAI_MODEL"] == DEFAULTS["PLATFORM_OPENAI_MODEL"]:
        if ai_env.get("OPENAI_MODEL"):
            values["PLATFORM_OPENAI_MODEL"] = ai_env["OPENAI_MODEL"]
    for key, nbytes in GENERATED_KEYS.items():
        values[key] = _token(nbytes)
    for key, val in existing.items():
        if key not in GENERATED_KEYS and key not in values:
            values[key] = val
    return values


def _format_env_file(values: dict[str, str]) -> str:
    lines: list[str] = []
    for key in API_ENV_TEMPLATE_KEYS:
        if key == "":
            lines.append("")
            continue
        lines.append(f"{key}={values.get(key, DEFAULTS.get(key, ''))}")
    return "\n".join(lines) + "\n"


def _write_env(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sync_ai_service_env(ai_env_path: Path, e2ee_token: str, existing_ai: dict[str, str]) -> None:
    lines: list[str] = []
    openai_keys = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_STT_MODEL",
        "OPENAI_TTS_MODEL",
        "OPENAI_TTS_VOICE",
    ]
    for key in openai_keys:
        val = existing_ai.get(key) or ""
        if val or key == "OPENAI_API_KEY":
            lines.append(f"{key}={val}")
    if lines:
        lines.append("")
    lines.extend(
        [
            "DJANGO_API_URL=http://127.0.0.1:8000",
            "E2EE_ENABLED=True",
            f"E2EE_INTERNAL_TOKEN={e2ee_token}",
            "",
        ]
    )
    _write_env(ai_env_path, "\n".join(lines))


class Command(BaseCommand):
    help = "Generate development secrets for apps/api/.env (and sync ai-service/.env)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--write",
            action="store_true",
            help="Write generated values to apps/api/.env and apps/ai-service/.env",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which keys would be regenerated without writing files",
        )
        parser.add_argument(
            "--force-email",
            action="store_true",
            help="Also regenerate PLATFORM_SMTP_PASSWORD / PLATFORM_IMAP_PASSWORD (default: preserve)",
        )

    def handle(self, *args, **options):
        api_env_path = Path(settings.BASE_DIR) / ".env"
        ai_env_path = Path(settings.BASE_DIR).parent / "ai-service" / ".env"
        existing = _parse_env_file(api_env_path)
        ai_existing = _parse_env_file(ai_env_path)
        values = _build_env_values(
            existing,
            force_email=options["force_email"],
            ai_env=ai_existing,
        )

        rotated = list(GENERATED_KEYS.keys())
        if options["force_email"]:
            rotated.extend(["PLATFORM_SMTP_PASSWORD", "PLATFORM_IMAP_PASSWORD"])

        if options["dry_run"]:
            self.stdout.write("Would regenerate: " + ", ".join(rotated))
            preserved = [k for k in PRESERVE_KEYS if existing.get(k)]
            if preserved:
                self.stdout.write("Would preserve: " + ", ".join(sorted(preserved)))
            return

        if not options["write"]:
            self.stdout.write(
                self.style.WARNING("Nothing written. Pass --write to update .env files.")
            )
            self.stdout.write("Would regenerate: " + ", ".join(rotated))
            return

        _write_env(api_env_path, _format_env_file(values))
        _sync_ai_service_env(
            ai_env_path,
            values["E2EE_INTERNAL_TOKEN"],
            _parse_env_file(ai_env_path),
        )
        self.stdout.write(self.style.SUCCESS(f"Wrote {api_env_path}"))
        self.stdout.write(self.style.SUCCESS(f"Wrote {ai_env_path}"))
        self.stdout.write("Regenerated: " + ", ".join(rotated))
        self.stdout.write(
            self.style.WARNING(
                "Run: python manage.py reset_env_encryption && scripts/dev-db-setup.ps1"
            )
        )
