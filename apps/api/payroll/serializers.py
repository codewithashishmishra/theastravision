from rest_framework import serializers
from .models import SalaryComponent, SalaryStructure, PayrollRun, Payslip

class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
