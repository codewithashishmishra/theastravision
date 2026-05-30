from rest_framework import serializers
from .models import LeaveType, LeavePolicy, LeaveBalance, LeaveRequest

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class LeavePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeavePolicy
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)

    class Meta:
        model = LeaveBalance
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def get_employee_name(self, obj):
        return f'{obj.employee.first_name} {obj.employee.last_name}'.strip()

class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
