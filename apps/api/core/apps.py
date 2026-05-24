from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  # noqa: F401
        import core.e2ee.models  # noqa: F401 — register REDIS table model

        from django.db import models
        from rest_framework import serializers

        from core.serializer_fields import RegionalDateTimeField

        serializers.ModelSerializer.serializer_field_mapping = {
            **serializers.ModelSerializer.serializer_field_mapping,
            models.DateTimeField: RegionalDateTimeField,
        }
