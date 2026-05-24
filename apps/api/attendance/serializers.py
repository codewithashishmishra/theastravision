from rest_framework import serializers
from .models import (
    Shift,
    GeoFence,
    AttendanceLog,
    AttendanceRegularization,
    AttendanceSettings,
    FieldLocationPing,
)


class AttendanceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSettings
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def validate_work_days(self, value):
        if value in (None, []):
            return [1, 2, 3, 4, 5]
        if not isinstance(value, list):
            raise serializers.ValidationError('work_days must be a list of ISO weekdays.')
        normalized = sorted({int(v) for v in value if 1 <= int(v) <= 7})
        if not normalized:
            raise serializers.ValidationError('At least one work day is required.')
        return normalized


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class GeoFenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoFence
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class AttendanceLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceLog
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def get_employee_name(self, obj):
        return f'{obj.employee.first_name} {obj.employee.last_name}'


class AttendanceRegularizationSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRegularization
        fields = '__all__'
        read_only_fields = ('tenant', 'id', 'approved_by', 'approved_at')

    def get_employee_name(self, obj):
        return f'{obj.employee.first_name} {obj.employee.last_name}'

    def get_approver_name(self, obj):
        if obj.approved_by:
            return f'{obj.approved_by.first_name} {obj.approved_by.last_name}'
        return None


class FieldLocationPingSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FieldLocationPing
        fields = '__all__'
        read_only_fields = ('tenant', 'id', 'recorded_at', 'employee', 'attendance_log', 'is_within_office_hours', 'near_home')

    def get_employee_name(self, obj):
        return f'{obj.employee.first_name} {obj.employee.last_name}'
