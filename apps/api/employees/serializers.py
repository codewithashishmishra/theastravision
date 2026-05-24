from rest_framework import serializers

from core.jurisdictions import jurisdiction_from_country, normalize_jurisdiction
from core.models import Tenant
from core.field_crypto import decrypt_sensitive, encrypt_sensitive, mask_sensitive
from .models import Employee, EmployeeContact, EmployeeBank, EmployeeTax, EmployeeTaxProfile, EmployeeDocument


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def validate(self, attrs):
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

        return attrs


class EmployeeContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeContact
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class EmployeeBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBank
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class EmployeeTaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTax
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


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
