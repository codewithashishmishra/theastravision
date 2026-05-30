import os

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import ConfigSettings, EnvConfiguration
from core.platform_config import MODULE_FRONTEND_DEBUG, MODULE_PLATFORM_UTILIZATION
from core.platform_email_env import (
    build_imap_config_from_env,
    build_smtp_config_from_env,
    platform_imap_password_from_env,
    platform_smtp_password_from_env,
)

FRONTEND_DEBUG_CONFIG = {
    "enabled": False,
}

PLATFORM_UTILIZATION_CONFIG = {
    "enabled": True,
    "cpu_threshold_percent": 80,
    "ram_threshold_percent": 80,
    "cooldown_duration_seconds": 300,
    "sample_interval_seconds": 30,
    "super_admin_bypass": False,
    "cooldown_message": (
        "System is cooling down. Please retry in about 5 minutes. "
        "Your changes are saved locally and will sync when the system is back."
    ),
}


class Command(BaseCommand):
    help = (
        "Seed encrypted EnvConfiguration modules for Super Admin platform settings. "
        "SMTP/IMAP are built from PLATFORM_SMTP_* / PLATFORM_IMAP_* env vars (cPanel SSL/TLS defaults). "
        "Set PLATFORM_SMTP_PASSWORD in .env before seeding."
    )

    def handle(self, *args, **options):
        ConfigSettings.get_or_create_key()
        self._seed_platform_utilization()
        self._seed_frontend_debug()
        self._seed_smtp()
        self._seed_imap()
        self._seed_ai()
        self.stdout.write(self.style.SUCCESS("Environment configuration seed complete"))

    def _seed_platform_utilization(self):
        obj, created = EnvConfiguration.objects.get_or_create(
            module=MODULE_PLATFORM_UTILIZATION,
        )
        existing = obj.get_config()
        if created or not existing:
            obj.set_config(PLATFORM_UTILIZATION_CONFIG)
            obj.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded {MODULE_PLATFORM_UTILIZATION} (CPU/RAM cooldown thresholds)"
                )
            )
        else:
            merged = {**PLATFORM_UTILIZATION_CONFIG, **existing}
            obj.set_config(merged)
            obj.save()
            self.stdout.write(
                f"Updated {MODULE_PLATFORM_UTILIZATION} (merged missing keys only)"
            )

    def _seed_frontend_debug(self):
        obj, created = EnvConfiguration.objects.get_or_create(
            module=MODULE_FRONTEND_DEBUG,
        )
        existing = obj.get_config()
        if created or not existing:
            obj.set_config(FRONTEND_DEBUG_CONFIG)
            obj.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded {MODULE_FRONTEND_DEBUG} (frontend HTTP debug logging)"
                )
            )
        else:
            merged = {**FRONTEND_DEBUG_CONFIG, **existing}
            obj.set_config(merged)
            obj.save()
            self.stdout.write(
                f"Updated {MODULE_FRONTEND_DEBUG} (merged missing keys only)"
            )

    def _merge_env_module(
        self,
        module: str,
        defaults: dict,
        *,
        env_password: str = '',
        preserve_password: bool = True,
        apply_defaults_over_existing: bool = False,
    ):
        obj, created = EnvConfiguration.objects.get_or_create(module=module)
        existing = obj.get_config()
        if created or not existing:
            merged = dict(defaults)
        elif apply_defaults_over_existing:
            conn_defaults = {k: v for k, v in defaults.items() if k != 'password'}
            merged = {**existing, **conn_defaults}
        else:
            merged = {**defaults, **existing}
        if env_password:
            merged['password'] = env_password
        elif preserve_password and existing.get('password'):
            merged['password'] = existing['password']
        obj.set_config(merged)
        obj.save()
        if created or not existing:
            self.stdout.write(self.style.SUCCESS(f'Seeded {module}'))
        else:
            self.stdout.write(f'Updated {module} (merged; password from env if set)')

    def _seed_smtp(self):
        defaults = build_smtp_config_from_env()
        env_password = platform_smtp_password_from_env()
        if not env_password:
            self.stdout.write(
                self.style.WARNING(
                    'PLATFORM_SMTP_PASSWORD is not set — SMTP password in DB may be empty. '
                    'Add it to apps/api/.env and re-run seed_env_config.'
                )
            )
        self._merge_env_module(
            'SMTP', defaults, env_password=env_password, apply_defaults_over_existing=True
        )

    def _seed_imap(self):
        defaults = build_imap_config_from_env()
        env_password = platform_imap_password_from_env()
        if not env_password:
            self.stdout.write(
                self.style.WARNING(
                    'PLATFORM_IMAP_PASSWORD / PLATFORM_SMTP_PASSWORD is not set — '
                    'IMAP password in DB may be empty.'
                )
            )
        self._merge_env_module(
            'IMAP', defaults, env_password=env_password, apply_defaults_over_existing=True
        )

    def _seed_ai(self):
        defaults = {
            'provider': 'openai',
            'api_key': '',
            'model': getattr(settings, 'PLATFORM_OPENAI_MODEL', 'gpt-5.4-mini'),
        }
        env_key = (
            os.environ.get('PLATFORM_OPENAI_API_KEY', '').strip()
            or getattr(settings, 'PLATFORM_OPENAI_API_KEY', '').strip()
        )
        if not env_key:
            self.stdout.write(
                self.style.WARNING(
                    'PLATFORM_OPENAI_API_KEY is not set — AI module api_key in DB may be empty. '
                    'Add it to apps/api/.env (or OPENAI_API_KEY in apps/ai-service/.env) and re-run seed_env_config.'
                )
            )
        obj, created = EnvConfiguration.objects.get_or_create(module='AI')
        existing = obj.get_config()
        if created or not existing:
            merged = dict(defaults)
        else:
            merged = {**defaults, **existing}
        if env_key:
            merged['api_key'] = env_key
        elif existing.get('api_key'):
            merged['api_key'] = existing['api_key']
        obj.set_config(merged)
        obj.save()
        if created or not existing:
            self.stdout.write(self.style.SUCCESS('Seeded AI (OpenAI platform config)'))
        else:
            self.stdout.write('Updated AI (merged; api_key from env if set)')
