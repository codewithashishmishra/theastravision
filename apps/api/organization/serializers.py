from rest_framework import serializers
from .models import CompanyProfile, Branch, Department, Designation, Grade, CostCenter, BusinessUnit, CompanyCalendar, Holiday, EmployeeCodeSequence

class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ('tenant', 'id')

class DesignationSerializer(serializers.ModelSerializer):
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
