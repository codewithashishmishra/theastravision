from rest_framework import serializers

from assets.models import AssetAssignment
from .models import Employee, EmployeeContact, EmployeeBank


class UserMeSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class EmployeeMeReadSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source='department.name', read_only=True, allow_null=True
    )
    designation_name = serializers.CharField(
        source='designation.name', read_only=True, allow_null=True
    )
    branch_name = serializers.CharField(source='branch.name', read_only=True, allow_null=True)

    class Meta:
        model = Employee
        fields = [
            'id',
            'employee_code',
            'first_name',
            'last_name',
            'date_of_birth',
            'date_of_joining',
            'status',
            'department_name',
            'designation_name',
            'branch_name',
        ]
        read_only_fields = fields


class EmployeeContactMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeContact
        fields = [
            'id',
            'personal_email',
            'mobile_number',
            'alternate_number',
            'present_address',
            'permanent_address',
            'emergency_contact_name',
            'emergency_contact_number',
        ]
        read_only_fields = ('id',)


class EmployeeContactMeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeContact
        fields = [
            'personal_email',
            'mobile_number',
            'alternate_number',
            'present_address',
            'permanent_address',
            'emergency_contact_name',
            'emergency_contact_number',
        ]
        extra_kwargs = {f: {'required': False} for f in fields}


class EmployeeBankMeSerializer(serializers.ModelSerializer):
    account_number_masked = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeBank
        fields = [
            'id',
            'bank_name',
            'account_number_masked',
            'ifsc_code',
            'account_type',
        ]
        read_only_fields = fields

    def get_account_number_masked(self, obj):
        num = obj.account_number or ''
        if len(num) <= 4:
            return '****'
        return f"{'*' * (len(num) - 4)}{num[-4:]}"


class MyAssetSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    serial_number = serializers.CharField(source='asset.serial_number', read_only=True)
    category = serializers.CharField(source='asset.category', read_only=True)
    asset_status = serializers.CharField(source='asset.status', read_only=True)

    class Meta:
        model = AssetAssignment
        fields = [
            'id',
            'assigned_date',
            'asset_name',
            'serial_number',
            'category',
            'asset_status',
        ]
        read_only_fields = fields
