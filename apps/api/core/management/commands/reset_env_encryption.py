from django.core.management.base import BaseCommand
from django.core.management import call_command

from core.models import ConfigSettings, EnvConfiguration


class Command(BaseCommand):
    help = (
        "Clear encrypted platform config (ConfigSettings + EnvConfiguration) and re-seed. "
        "Use after changing SECRET_KEY or TRACKER_MASTER_KEY, or when seeing cryptography InvalidTag."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-seed",
            action="store_true",
            help="Only delete encrypted rows; do not run seed_env_config.",
        )

    def handle(self, *args, **options):
        n_config = ConfigSettings.objects.count()
        n_env = EnvConfiguration.objects.count()
        ConfigSettings.objects.all().delete()
        EnvConfiguration.objects.all().delete()
        EnvConfiguration.get_cached_config.cache_clear()
        self.stdout.write(
            self.style.WARNING(
                f"Deleted {n_config} ConfigSettings and {n_env} EnvConfiguration row(s)."
            )
        )
        if options["no_seed"]:
            self.stdout.write("Skipped seed_env_config (--no-seed).")
            return
        call_command("seed_env_config")
        self.stdout.write(self.style.SUCCESS("Encryption reset and env config re-seeded."))
