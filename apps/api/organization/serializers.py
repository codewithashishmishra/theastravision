from rest_framework import serializers

from core.tenant_utils import resolve_request_tenant_id
from .models import (
    CompanyProfile,
    LegalEntity,
    Branch,
    Department,
    Designation,
    Grade,
    CostCenter,
    BusinessUnit,
    CompanyCalendar,
    Holiday,
    EmployeeCodeSequence,
)


class TenantCodeUniqueMixin:
    """Validate code uniqueness within the request tenant."""

    tenant_code_model = None
    tenant_code_field_label = 'code'

    def validate_code(self, value):
        code = (value or '').strip()
        if not code:
            raise serializers.ValidationError('Code is required.')

        request = self.context.get('request')
        tenant_id = resolve_request_tenant_id(request) if request else None
        if not tenant_id and self.instance:
            tenant_id = self.instance.tenant_id
        if not tenant_id:
            return code

        model = self.tenant_code_model or self.Meta.model
        qs = model.objects.filter(tenant_id=tenant_id, code__iexact=code)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f'A {self.tenant_code_field_label} with this code already exists.'
            )
        return code


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class LegalEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalEntity
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class BranchSerializer(TenantCodeUniqueMixin, serializers.ModelSerializer):
    tenant_code_field_label = 'branch'

    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        lat = attrs.get('latitude', getattr(self.instance, 'latitude', None))
        lng = attrs.get('longitude', getattr(self.instance, 'longitude', None))
        if lat is not None and lng is None:
            raise serializers.ValidationError({'longitude': 'Both latitude and longitude are required for office location.'})
        if lng is not None and lat is None:
            raise serializers.ValidationError({'latitude': 'Both latitude and longitude are required for office location.'})
        return attrs


class DepartmentSerializer(TenantCodeUniqueMixin, serializers.ModelSerializer):
    tenant_code_field_label = 'department'

    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class DesignationSerializer(TenantCodeUniqueMixin, serializers.ModelSerializer):
    tenant_code_field_label = 'designation'

    class Meta:
        model = Designation
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class CompanyCalendarSerializer(serializers.ModelSerializer):
    holidays = HolidaySerializer(many=True, read_only=True)

    class Meta:
        model = CompanyCalendar
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class EmployeeCodeSequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCodeSequence
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
