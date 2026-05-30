from django.apps import AppConfig


class OffboardingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'offboarding'

    def ready(self):
        import offboarding.signals  # noqa: F401
