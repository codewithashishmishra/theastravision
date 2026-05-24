from rest_framework import serializers
from .models import Employee, EmployeeContact, EmployeeBank, EmployeeTax, EmployeeDocument

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

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

class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'
        read_only_fields = ('tenant', 'id')
