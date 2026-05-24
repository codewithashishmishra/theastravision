from rest_framework import serializers

from core.jurisdictions import jurisdiction_from_country, normalize_jurisdiction
from core.models import Tenant
from core.field_crypto import (
    decrypt_sensitive,
    encrypt_sensitive,
    encrypt_stored_field,
    mask_sensitive,
    mask_stored_field,
)
from .models import Employee, EmployeeContact, EmployeeBank, EmployeeTax, EmployeeTaxProfile, EmployeeDocument
from .org_utils import (
    avatar_url_for_employee,
    employee_display_name,
    employee_initials,
    reporting_manager_would_cycle,
    role_names_for_employee,
)


class EmployeeSerializer(serializers.ModelSerializer):
    employee_type_name = serializers.CharField(source='employee_type.name', read_only=True)
    home_location_complete = serializers.SerializerMethodField()
    reporting_manager_name = serializers.SerializerMethodField()
    designation_name = serializers.CharField(
        source='designation.name', read_only=True, allow_null=True
    )
    role_names = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('tenant', 'id', 'office_location_verified_at')

    def get_home_location_complete(self, obj):
        try:
            return obj.work_location.has_home_coordinates()
        except Exception:
            return False

    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager_id and obj.reporting_manager:
            return employee_display_name(obj.reporting_manager)
        return None

    def get_role_names(self, obj):
        return role_names_for_employee(obj)

    def get_avatar_url(self, obj):
        return avatar_url_for_employee(obj)

    def get_initials(self, obj):
        return employee_initials(obj.first_name, obj.last_name)

    def _validate_reporting_manager(self, attrs):
        tenant_id = self.context.get('tenant_id') or getattr(self.instance, 'tenant_id', None)
        if not tenant_id:
            return

        manager = attrs.get('reporting_manager')
        if manager is None and 'reporting_manager' not in attrs:
            if self.instance is not None:
                manager = self.instance.reporting_manager
            else:
                manager = None

        employee_id = getattr(self.instance, 'pk', None)

        if self.instance is None:
            has_employees = Employee.objects.filter(tenant_id=tenant_id).exists()
            if has_employees and not manager:
                raise serializers.ValidationError(
                    {'reporting_manager': 'Reporting manager is required (except for the first root employee).'}
                )
        else:
            if 'reporting_manager' in attrs and manager is None:
                has_reportees = Employee.objects.filter(
                    tenant_id=tenant_id, reporting_manager_id=self.instance.pk
                ).exists()
                if has_reportees:
                    raise serializers.ValidationError(
                        {'reporting_manager': 'Cannot remove manager while this employee has direct reportees.'}
                    )

        if manager is None:
            return

        if str(manager.tenant_id) != str(tenant_id):
            raise serializers.ValidationError(
                {'reporting_manager': 'Manager must belong to the same organization.'}
            )

        if manager.status != 'Active':
            raise serializers.ValidationError(
                {'reporting_manager': 'Reporting manager must be an active employee.'}
            )

        if employee_id and str(manager.pk) == str(employee_id):
            raise serializers.ValidationError(
                {'reporting_manager': 'An employee cannot be their own reporting manager.'}
            )

        if employee_id and reporting_manager_would_cycle(employee_id, manager.pk):
            raise serializers.ValidationError(
                {'reporting_manager': 'This reporting manager assignment would create a cycle.'}
            )

    def validate(self, attrs):
        if self.instance is None and not attrs.get('employee_type') and not attrs.get('employee_type_id'):
            raise serializers.ValidationError({'employee_type': 'Employee type is required.'})
        tenant_id = self.context.get('tenant_id') or getattr(self.instance, 'tenant_id', None)
        payroll_jurisdiction = attrs.get('payroll_jurisdiction') or getattr(
            self.instance, 'payroll_jurisdiction', 'IN'
        )
        legal_entity = attrs.get('legal_entity') or getattr(self.instance, 'legal_entity', None)
        branch = attrs.get('branch') or getattr(self.instance, 'branch', None)

        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id).first()
            if tenant and payroll_jurisdiction not in (tenant.enabled_jurisdictions or ['IN']):
                raise serializers.ValidationError(
                    {'payroll_jurisdiction': 'Jurisdiction not enabled for this tenant.'}
                )

        if legal_entity and legal_entity.jurisdiction != payroll_jurisdiction:
            raise serializers.ValidationError(
                {'legal_entity': 'Legal entity jurisdiction must match employee payroll jurisdiction.'}
            )

        if not attrs.get('payroll_jurisdiction') and branch and not getattr(self.instance, 'payroll_jurisdiction', None):
            attrs['payroll_jurisdiction'] = jurisdiction_from_country(branch.country)

        self._validate_reporting_manager(attrs)

        return attrs


class EmployeeContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeContact
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class EmployeeBankSerializer(serializers.ModelSerializer):
    SENSITIVE_FIELDS = ('account_number',)

    class Meta:
        model = EmployeeBank
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in self.SENSITIVE_FIELDS:
            if data.get(key):
                data[key] = mask_stored_field(data[key], f'bank_{key}')
        return data

    def _encrypt_fields(self, validated_data):
        for key in self.SENSITIVE_FIELDS:
            if key in validated_data and validated_data[key]:
                validated_data[key] = encrypt_stored_field(validated_data[key], f'bank_{key}')
        return validated_data

    def create(self, validated_data):
        self._encrypt_fields(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._encrypt_fields(validated_data)
        return super().update(instance, validated_data)


class EmployeeTaxSerializer(serializers.ModelSerializer):
    SENSITIVE_FIELDS = ('pan_number', 'aadhaar_number', 'uan_number', 'pf_number', 'esic_number')

    class Meta:
        model = EmployeeTax
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in self.SENSITIVE_FIELDS:
            if data.get(key):
                data[key] = mask_stored_field(data[key], key)
        return data

    def _encrypt_fields(self, validated_data):
        for key in self.SENSITIVE_FIELDS:
            if key in validated_data and validated_data[key]:
                validated_data[key] = encrypt_stored_field(validated_data[key], key)
        return validated_data

    def create(self, validated_data):
        self._encrypt_fields(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._encrypt_fields(validated_data)
        return super().update(instance, validated_data)


def _encrypt_profile_fields(fields: dict) -> dict:
    result = dict(fields or {})
    for key in ('ssn', 'sin'):
        val = result.get(key)
        if val and not str(val).startswith('enc:'):
            result[key] = 'enc:' + encrypt_sensitive(str(val), key)
    return result


def _decrypt_profile_value(value: str, key: str) -> str:
    if not value:
        return ''
    stored = str(value)[4:] if str(value).startswith('enc:') else str(value)
    return decrypt_sensitive(stored, key)


class EmployeeTaxProfileSerializer(serializers.ModelSerializer):
    masked_fields = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeTaxProfile
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def get_masked_fields(self, obj):
        fields = dict(obj.fields or {})
        for key in ('ssn', 'sin'):
            if fields.get(key):
                fields[key] = mask_sensitive(_decrypt_profile_value(fields[key], key))
        return fields

    def validate(self, attrs):
        employee = attrs.get('employee') or self.instance.employee
        jurisdiction = attrs.get('jurisdiction') or self.instance.jurisdiction
        if employee and employee.payroll_jurisdiction != jurisdiction:
            raise serializers.ValidationError(
                {'jurisdiction': 'Tax profile jurisdiction must match employee payroll jurisdiction.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data['fields'] = _encrypt_profile_fields(validated_data.get('fields'))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'fields' in validated_data:
            merged = dict(instance.fields or {})
            merged.update(_encrypt_profile_fields(validated_data.get('fields')))
            validated_data['fields'] = merged
        return super().update(instance, validated_data)


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
