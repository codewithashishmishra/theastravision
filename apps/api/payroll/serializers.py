from rest_framework import serializers

from .models import (
    SalaryComponent,
    SalaryStructure,
    PayrollRun,
    Payslip,
    PayrollLineItem,
    TaxDeclaration,
)


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class SalaryStructureSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SalaryStructure
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def get_employee_name(self, obj):
        return f'{obj.employee.first_name} {obj.employee.last_name}'

    def validate(self, attrs):
        tenant = self.context['request'].user.tenant
        if not tenant:
            return attrs
        var_enabled = attrs.get('variable_pay_enabled', getattr(self.instance, 'variable_pay_enabled', None))
        var_amount = attrs.get('variable_pay_amount', getattr(self.instance, 'variable_pay_amount', None))
        var_pct = attrs.get('variable_pay_pct', getattr(self.instance, 'variable_pay_pct', None))
        if var_enabled and not tenant.variable_pay_enabled:
            raise serializers.ValidationError('Variable pay is disabled at company level.')
        if (var_amount or var_pct) and not tenant.variable_pay_enabled:
            raise serializers.ValidationError('Enable variable pay in payroll settings first.')
        return attrs


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class PayrollLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollLineItem
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class PayslipSerializer(serializers.ModelSerializer):
    line_items = PayrollLineItemSerializer(many=True, read_only=True)
    month = serializers.IntegerField(source='payroll_run.month', read_only=True)
    year = serializers.IntegerField(source='payroll_run.year', read_only=True)

    class Meta:
        model = Payslip
        fields = '__all__'
        read_only_fields = ('tenant', 'id')


class TaxDeclarationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxDeclaration
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

    def validate_sections(self, value):
        if isinstance(value, str):
            import json
            return json.loads(value or '{}')
        return value or {}
