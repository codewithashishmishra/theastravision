from rest_framework import serializers

from core.regional_serializers import RegionalModelSerializer
from .models import Notification, NotificationPreference


class NotificationSerializer(RegionalModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
