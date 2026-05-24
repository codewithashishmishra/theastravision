from rest_framework import viewsets
from core.permissions import IsAuthenticatedTenantUser
from core.tenant_utils import attach_tenant_to_request
from .models import CompanyProfile, Branch, Department, Designation, Grade, CostCenter, BusinessUnit, CompanyCalendar, Holiday, EmployeeCodeSequence
from .serializers import (
    CompanyProfileSerializer, BranchSerializer, DepartmentSerializer, 
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
        tenant_id = getattr(self.request, 'tenant_id', None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        if self.request.user.is_superuser:
            return self.queryset.all()
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, 'tenant_id', None)
        if not tenant_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("No tenant assigned to your account.")
        serializer.save(tenant_id=tenant_id)

class CompanyProfileViewSet(BaseTenantViewSet):
    queryset = CompanyProfile.objects.all()
    serializer_class = CompanyProfileSerializer
    search_fields = ['legal_name', 'registration_number', 'tax_id']

class BranchViewSet(BaseTenantViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

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
