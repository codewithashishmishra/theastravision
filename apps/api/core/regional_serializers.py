from django.db import models
from rest_framework import serializers

from core.serializer_fields import RegionalDateTimeField


class RegionalModelSerializer(serializers.ModelSerializer):
    """ModelSerializer that emits datetimes in the viewer's activated regional timezone."""

    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.DateTimeField: RegionalDateTimeField,
    }
