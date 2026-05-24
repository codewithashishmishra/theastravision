from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import UserRoleMapping
from core.tenant_utils import resolve_request_tenant_id
from organization.views import AuditedTenantViewSet

from .models import (
    Employee,
    EmployeeContact,
    EmployeeBank,
    EmployeeTax,
    EmployeeTaxProfile,
    EmployeeDocument,
    EmployeeType,
)
from .org_utils import build_org_tree_nodes
from .serializers import (
    EmployeeSerializer,
    EmployeeContactSerializer,
    EmployeeBankSerializer,
    EmployeeTaxSerializer,
    EmployeeTaxProfileSerializer,
    EmployeeDocumentSerializer,
)
from .serializers_types import EmployeeTypeSerializer


class EmployeeViewSet(AuditedTenantViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    audit_module = "employees"
    audit_resource = "employee"
    search_fields = ['first_name', 'last_name', 'employee_code', 'user__email']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            'designation',
            'reporting_manager',
            'employee_type',
            'user',
        ).prefetch_related(
            Prefetch(
                'user__role_mappings',
                queryset=UserRoleMapping.objects.select_related('role'),
            ),
            'documents',
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['tenant_id'] = resolve_request_tenant_id(self.request)
        return ctx

    @action(detail=False, methods=['get'], url_path='org-tree')
    def org_tree(self, request):
        tenant_id = resolve_request_tenant_id(request)
        if not tenant_id:
            return Response(
                {'detail': 'Tenant context required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        employees = list(
            Employee.objects.filter(tenant_id=tenant_id, status='Active')
            .select_related('designation', 'user', 'reporting_manager')
            .prefetch_related(
                Prefetch(
                    'user__role_mappings',
                    queryset=UserRoleMapping.objects.select_related('role'),
                ),
                'documents',
            )
            .order_by('first_name', 'last_name')
        )
        roots, total = build_org_tree_nodes(employees)
        return Response({'roots': roots, 'meta': {'total': total}})


class EmployeeContactViewSet(AuditedTenantViewSet):
    queryset = EmployeeContact.objects.all()
    serializer_class = EmployeeContactSerializer
    audit_module = "employees"
    audit_resource = "employee_contact"


class EmployeeBankViewSet(AuditedTenantViewSet):
    queryset = EmployeeBank.objects.all()
    serializer_class = EmployeeBankSerializer
    audit_module = "employees"
    audit_resource = "employee_bank"


class EmployeeTaxViewSet(AuditedTenantViewSet):
    queryset = EmployeeTax.objects.all()
    serializer_class = EmployeeTaxSerializer
    audit_module = "employees"
    audit_resource = "employee_tax"


class EmployeeTaxProfileViewSet(AuditedTenantViewSet):
    queryset = EmployeeTaxProfile.objects.all()
    serializer_class = EmployeeTaxProfileSerializer
    audit_module = "employees"
    audit_resource = "employee_tax_profile"

    def get_queryset(self):
        qs = super().get_queryset()
        jurisdiction = self.request.query_params.get('jurisdiction')
        employee_id = self.request.query_params.get('employee')
        if jurisdiction:
            qs = qs.filter(jurisdiction=jurisdiction)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs


class EmployeeDocumentViewSet(AuditedTenantViewSet):
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
    audit_module = "employees"
    audit_resource = "employee_document"


class EmployeeTypeViewSet(AuditedTenantViewSet):
    queryset = EmployeeType.objects.all()
    serializer_class = EmployeeTypeSerializer
    audit_module = "employees"
    audit_resource = "employee_type"
    search_fields = ['name', 'code']
