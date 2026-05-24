from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from core.permissions import IsAuthenticatedTenantUser
from core.audit import AuditViewSetMixin
from core.tenant_utils import attach_tenant_to_request, resolve_request_tenant_id
from .models import CompanyProfile, LegalEntity, Branch, Department, Designation, Grade, CostCenter, BusinessUnit, CompanyCalendar, Holiday, EmployeeCodeSequence
from .serializers import (
    CompanyProfileSerializer, LegalEntitySerializer, BranchSerializer, DepartmentSerializer,
    DesignationSerializer, GradeSerializer, CostCenterSerializer,
    BusinessUnitSerializer, CompanyCalendarSerializer, HolidaySerializer,
    EmployeeCodeSequenceSerializer
)

class BaseTenantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedTenantUser]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        attach_tenant_to_request(request)

    def get_queryset(self):
        tenant_id = resolve_request_tenant_id(self.request)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = resolve_request_tenant_id(self.request)
        if not tenant_id:
            raise ValidationError("No tenant assigned to your account.")
        serializer.save(tenant_id=tenant_id)


class AuditedTenantViewSet(AuditViewSetMixin, BaseTenantViewSet):
    """Tenant-scoped CRUD with SystemAuditLog entries."""

    audit_module = "hrms"

class CompanyProfileViewSet(BaseTenantViewSet):
    queryset = CompanyProfile.objects.all()
    serializer_class = CompanyProfileSerializer
    search_fields = ['legal_name', 'registration_number', 'tax_id']


class LegalEntityViewSet(BaseTenantViewSet):
    queryset = LegalEntity.objects.all()
    serializer_class = LegalEntitySerializer
    search_fields = ['legal_name', 'tax_id', 'jurisdiction']

class BranchViewSet(BaseTenantViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)
        from organization.services.branch_geofence import sync_branch_geofence
        sync_branch_geofence(serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        from organization.services.branch_geofence import sync_branch_geofence
        sync_branch_geofence(serializer.instance)

class DepartmentViewSet(BaseTenantViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

class DesignationViewSet(BaseTenantViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer

class GradeViewSet(BaseTenantViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class CostCenterViewSet(BaseTenantViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer

class BusinessUnitViewSet(BaseTenantViewSet):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer

class CompanyCalendarViewSet(BaseTenantViewSet):
    queryset = CompanyCalendar.objects.all()
    serializer_class = CompanyCalendarSerializer

class HolidayViewSet(BaseTenantViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer

class EmployeeCodeSequenceViewSet(BaseTenantViewSet):
    queryset = EmployeeCodeSequence.objects.all()
    serializer_class = EmployeeCodeSequenceSerializer
