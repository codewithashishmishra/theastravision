from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.tenant_utils import resolve_request_tenant_id
from organization.views import BaseTenantViewSet

from .models import Employee, EmployeeContact, EmployeeBank, EmployeeTax, EmployeeTaxProfile, EmployeeDocument
from .serializers import (
    EmployeeSerializer,
    EmployeeContactSerializer,
    EmployeeBankSerializer,
    EmployeeTaxSerializer,
    EmployeeTaxProfileSerializer,
    EmployeeDocumentSerializer,
)


class EmployeeViewSet(BaseTenantViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    search_fields = ['first_name', 'last_name', 'employee_code', 'user__email']

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['tenant_id'] = resolve_request_tenant_id(self.request)
        return ctx


class EmployeeContactViewSet(BaseTenantViewSet):
    queryset = EmployeeContact.objects.all()
    serializer_class = EmployeeContactSerializer


class EmployeeBankViewSet(BaseTenantViewSet):
    queryset = EmployeeBank.objects.all()
    serializer_class = EmployeeBankSerializer


class EmployeeTaxViewSet(BaseTenantViewSet):
    queryset = EmployeeTax.objects.all()
    serializer_class = EmployeeTaxSerializer


class EmployeeTaxProfileViewSet(BaseTenantViewSet):
    queryset = EmployeeTaxProfile.objects.all()
    serializer_class = EmployeeTaxProfileSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        jurisdiction = self.request.query_params.get('jurisdiction')
        employee_id = self.request.query_params.get('employee')
        if jurisdiction:
            qs = qs.filter(jurisdiction=jurisdiction)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs


class EmployeeDocumentViewSet(BaseTenantViewSet):
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
