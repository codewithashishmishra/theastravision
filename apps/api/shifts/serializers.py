from rest_framework import serializers
from .models import RosterAssignment, ShiftSwapRequest, OvertimeRequest

class RosterAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RosterAssignment
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class ShiftSwapRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSwapRequest
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class OvertimeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimeRequest
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
