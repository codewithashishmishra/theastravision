from rest_framework import viewsets, permissions
from .models import Employee, EmployeeContact, EmployeeBank, EmployeeTax, EmployeeDocument
from .serializers import (
    EmployeeSerializer, EmployeeContactSerializer, 
    EmployeeBankSerializer, EmployeeTaxSerializer, EmployeeDocumentSerializer
)
from organization.views import BaseTenantViewSet

class EmployeeViewSet(BaseTenantViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    search_fields = ['first_name', 'last_name', 'employee_code', 'user__email']

class EmployeeContactViewSet(BaseTenantViewSet):
    queryset = EmployeeContact.objects.all()
    serializer_class = EmployeeContactSerializer

class EmployeeBankViewSet(BaseTenantViewSet):
    queryset = EmployeeBank.objects.all()
    serializer_class = EmployeeBankSerializer

class EmployeeTaxViewSet(BaseTenantViewSet):
    queryset = EmployeeTax.objects.all()
    serializer_class = EmployeeTaxSerializer

class EmployeeDocumentViewSet(BaseTenantViewSet):
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
