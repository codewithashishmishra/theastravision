from rest_framework import serializers

from organization.serializers import TenantCodeUniqueMixin
from .models import EmployeeType, EmployeeWorkLocation


class EmployeeTypeSerializer(TenantCodeUniqueMixin, serializers.ModelSerializer):
    tenant_code_field_label = 'employee type'

    class Meta:
        model = EmployeeType
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def validate_tracking_interval_minutes(self, value):
        if value is None:
            return 10
        return max(5, min(15, int(value)))


class EmployeeWorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeWorkLocation
        fields = (
            'id',
            'home_address',
            'home_latitude',
            'home_longitude',
            'completed_at',
        )
        read_only_fields = ('id', 'completed_at')

    def validate(self, attrs):
        lat = attrs.get('home_latitude')
        lng = attrs.get('home_longitude')
        if lat is not None and lng is None:
            raise serializers.ValidationError({'home_longitude': 'Both latitude and longitude are required.'})
        if lng is not None and lat is None:
            raise serializers.ValidationError({'home_latitude': 'Both latitude and longitude are required.'})
        return attrs
