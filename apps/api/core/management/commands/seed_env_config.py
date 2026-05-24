from django.core.management.base import BaseCommand

from core.models import ConfigSettings, EnvConfiguration
from core.platform_config import MODULE_PLATFORM_UTILIZATION

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
    help = "Seed encrypted EnvConfiguration modules for Super Admin platform settings"

    def handle(self, *args, **options):
        ConfigSettings.get_or_create_key()
        self._seed_platform_utilization()
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
