import json

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Tenant
from core.permissions import IsAuthenticatedTenantUser
from core.tenant_utils import attach_tenant_to_request, resolve_request_tenant_id
from employees.models import Employee
from organization.views import BaseTenantViewSet
from payroll.models import Payslip

from .models import StatutoryRuleSet, ComplianceDocument, FilingRecord
from .serializers import StatutoryRuleSetSerializer, ComplianceDocumentSerializer, FilingRecordSerializer
from .services import (
    generate_form16_pdf,
    generate_form12ba_pdf,
    generate_w2_pdf,
    generate_1095c_pdf,
    generate_t4_pdf,
    generate_rl1_pdf,
    generate_ecr_csv,
    generate_941_export,
    generate_itr_assist,
    generate_us_1040_prep,
    generate_ca_t1_prep,
    save_compliance_document,
)


class StatutoryRuleSetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StatutoryRuleSet.objects.all()
    serializer_class = StatutoryRuleSetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        jurisdiction = self.request.query_params.get('jurisdiction')
        if jurisdiction:
            qs = qs.filter(jurisdiction=jurisdiction)
        return qs


class ComplianceDocumentViewSet(BaseTenantViewSet):
    queryset = ComplianceDocument.objects.all()
    serializer_class = ComplianceDocumentSerializer


class FilingRecordViewSet(BaseTenantViewSet):
    queryset = FilingRecord.objects.all()
    serializer_class = FilingRecordSerializer


class ComplianceActionViewSet(viewsets.ViewSet):
    """Compliance generation and export actions."""

    permission_classes = [IsAuthenticatedTenantUser]

    def initial(self, request, *args, **kwargs):
        attach_tenant_to_request(request)
        return super().initial(request, *args, **kwargs)

    def _tenant_id(self, request):
        return resolve_request_tenant_id(request)

    def _fy_payslips(self, tenant_id, employee, jurisdiction, fy):
        return Payslip.objects.filter(
            tenant_id=tenant_id,
            employee=employee,
            jurisdiction=jurisdiction,
            payroll_run__year__gte=fy if jurisdiction == 'IN' else fy,
            payroll_run__year__lte=fy + 1 if jurisdiction == 'IN' else fy,
        ).prefetch_related('line_items')

    @action(detail=False, methods=['post'], url_path='form16/generate')
    def form16_generate(self, request):
        tenant_id = self._tenant_id(request)
        fy = int(request.data.get('fy', 2025))
        employee_id = request.data.get('employee_id')
        employees = Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='IN')
        if employee_id:
            employees = employees.filter(id=employee_id)
        created = []
        tenant = Tenant.objects.get(id=tenant_id)
        for emp in employees:
            payslips = self._fy_payslips(tenant_id, emp, 'IN', fy)
            pdf, meta = generate_form16_pdf(tenant, emp, emp.legal_entity, fy, payslips)
            doc = save_compliance_document(tenant_id, emp, 'IN', 'FORM16', fy, pdf, meta)
            created.append(str(doc.id))
        return Response({'generated': len(created), 'document_ids': created})

    @action(detail=False, methods=['post'], url_path='form12ba/generate')
    def form12ba_generate(self, request):
        tenant_id = self._tenant_id(request)
        fy = int(request.data.get('fy', 2025))
        perks = request.data.get('perquisites', {})
        employee_id = request.data.get('employee_id')
        employees = Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='IN')
        if employee_id:
            employees = employees.filter(id=employee_id)
        created = []
        tenant = Tenant.objects.get(id=tenant_id)
        for emp in employees:
            emp_perks = perks.get(str(emp.id), perks) if isinstance(perks, dict) else {}
            pdf, meta = generate_form12ba_pdf(tenant, emp, emp.legal_entity, fy, emp_perks)
            doc = save_compliance_document(tenant_id, emp, 'IN', 'FORM12BA', fy, pdf, meta)
            created.append(str(doc.id))
        return Response({'generated': len(created), 'document_ids': created})

    @action(detail=False, methods=['post'], url_path='w2/generate')
    def w2_generate(self, request):
        tenant_id = self._tenant_id(request)
        tax_year = int(request.data.get('tax_year', 2025))
        employee_id = request.data.get('employee_id')
        employees = Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='US')
        if employee_id:
            employees = employees.filter(id=employee_id)
        created = []
        tenant = Tenant.objects.get(id=tenant_id)
        for emp in employees:
            payslips = Payslip.objects.filter(
                tenant_id=tenant_id, employee=emp, jurisdiction='US', payroll_run__year=tax_year
            ).prefetch_related('line_items')
            pdf, meta = generate_w2_pdf(tenant, emp, emp.legal_entity, tax_year, payslips)
            doc = save_compliance_document(tenant_id, emp, 'US', 'W2', tax_year, pdf, meta)
            created.append(str(doc.id))
        return Response({'generated': len(created), 'document_ids': created})

    @action(detail=False, methods=['post'], url_path='1095c/generate')
    def form1095c_generate(self, request):
        tenant_id = self._tenant_id(request)
        tax_year = int(request.data.get('tax_year', 2025))
        offer_code = request.data.get('offer_of_coverage', '1A')
        employee_id = request.data.get('employee_id')
        employees = Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='US')
        if employee_id:
            employees = employees.filter(id=employee_id)
        created = []
        tenant = Tenant.objects.get(id=tenant_id)
        for emp in employees:
            pdf, meta = generate_1095c_pdf(tenant, emp, emp.legal_entity, tax_year, offer_code)
            doc = save_compliance_document(tenant_id, emp, 'US', 'FORM1095C', tax_year, pdf, meta)
            created.append(str(doc.id))
        return Response({'generated': len(created), 'document_ids': created})

    @action(detail=False, methods=['post'], url_path='t4/generate')
    def t4_generate(self, request):
        tenant_id = self._tenant_id(request)
        tax_year = int(request.data.get('tax_year', 2025))
        employee_id = request.data.get('employee_id')
        employees = Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='CA')
        if employee_id:
            employees = employees.filter(id=employee_id)
        created = []
        tenant = Tenant.objects.get(id=tenant_id)
        for emp in employees:
            payslips = Payslip.objects.filter(
                tenant_id=tenant_id, employee=emp, jurisdiction='CA', payroll_run__year=tax_year
            ).prefetch_related('line_items')
            pdf, meta = generate_t4_pdf(tenant, emp, emp.legal_entity, tax_year, payslips)
            doc = save_compliance_document(tenant_id, emp, 'CA', 'T4', tax_year, pdf, meta)
            created.append(str(doc.id))
        return Response({'generated': len(created), 'document_ids': created})

    @action(detail=False, methods=['post'], url_path='rl1/generate')
    def rl1_generate(self, request):
        tenant_id = self._tenant_id(request)
        tax_year = int(request.data.get('tax_year', 2025))
        employee_id = request.data.get('employee_id')
        employees = Employee.objects.filter(tenant_id=tenant_id, payroll_jurisdiction='CA')
        if employee_id:
            employees = employees.filter(id=employee_id)
        created = []
        tenant = Tenant.objects.get(id=tenant_id)
        for emp in employees:
            branch = emp.branch
            state = (branch.state or '').upper() if branch else ''
            profile = emp.tax_profiles.filter(jurisdiction='CA').first()
            prov_fields = profile.fields if profile else {}
            if state not in ('QC', 'QUEBEC') and prov_fields.get('province', '').upper() not in ('QC', 'QUEBEC'):
                continue
            payslips = Payslip.objects.filter(
                tenant_id=tenant_id, employee=emp, jurisdiction='CA', payroll_run__year=tax_year
            ).prefetch_related('line_items')
            pdf, meta = generate_rl1_pdf(tenant, emp, emp.legal_entity, tax_year, payslips)
            doc = save_compliance_document(tenant_id, emp, 'CA', 'RL1', tax_year, pdf, meta)
            created.append(str(doc.id))
        return Response({'generated': len(created), 'document_ids': created})

    @action(detail=False, methods=['post'], url_path='bulk-year-end')
    def bulk_year_end(self, request):
        """Queue Celery bulk generation for all jurisdictions enabled on tenant."""
        from compliance.tasks import bulk_generate_year_end_documents

        tenant_id = self._tenant_id(request)
        fy = int(request.data.get('fy', request.data.get('tax_year', 2025)))
        bulk_generate_year_end_documents.delay(str(tenant_id), fy)
        return Response({'status': 'queued', 'fy': fy})

    @action(detail=False, methods=['post'], url_path='ecr/export')
    def ecr_export(self, request):
        tenant_id = self._tenant_id(request)
        month = int(request.data.get('month', 1))
        year = int(request.data.get('year', 2025))
        csv_data = generate_ecr_csv(tenant_id, 'IN', month, year)
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="ecr_{year}_{month}.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='941/export')
    def form941_export(self, request):
        tenant_id = self._tenant_id(request)
        quarter = int(request.data.get('quarter', 1))
        year = int(request.data.get('year', 2025))
        csv_data = generate_941_export(tenant_id, 'US', quarter, year)
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="941_q{quarter}_{year}.csv"'
        return response

    @action(detail=False, methods=['post'], url_path='itr-assist')
    def itr_assist(self, request):
        tenant_id = self._tenant_id(request)
        fy = int(request.data.get('fy', 2025))
        employee_id = request.data.get('employee_id')
        emp = Employee.objects.get(tenant_id=tenant_id, id=employee_id)
        tenant = Tenant.objects.get(id=tenant_id)
        payslips = Payslip.objects.filter(tenant_id=tenant_id, employee=emp, jurisdiction='IN').prefetch_related(
            'line_items'
        )
        data = generate_itr_assist(tenant, emp, fy, payslips)
        content = json.dumps(data, indent=2).encode('utf-8')
        doc = save_compliance_document(tenant_id, emp, 'IN', 'ITR_ASSIST', fy, content, data, ext='json')
        return Response({'document_id': str(doc.id), 'data': data})

    @action(detail=False, methods=['post'], url_path='us-1040-prep')
    def us_1040_prep(self, request):
        tenant_id = self._tenant_id(request)
        tax_year = int(request.data.get('tax_year', 2025))
        employee_id = request.data.get('employee_id')
        emp = Employee.objects.get(tenant_id=tenant_id, id=employee_id)
        tenant = Tenant.objects.get(id=tenant_id)
        payslips = Payslip.objects.filter(
            tenant_id=tenant_id, employee=emp, jurisdiction='US', payroll_run__year=tax_year
        ).prefetch_related('line_items')
        data = generate_us_1040_prep(tenant, emp, tax_year, payslips)
        content = json.dumps(data, indent=2).encode('utf-8')
        doc = save_compliance_document(tenant_id, emp, 'US', 'US_1040_PREP', tax_year, content, data, ext='json')
        return Response({'document_id': str(doc.id), 'data': data})

    @action(detail=False, methods=['post'], url_path='ca-t1-prep')
    def ca_t1_prep(self, request):
        tenant_id = self._tenant_id(request)
        tax_year = int(request.data.get('tax_year', 2025))
        employee_id = request.data.get('employee_id')
        emp = Employee.objects.get(tenant_id=tenant_id, id=employee_id)
        tenant = Tenant.objects.get(id=tenant_id)
        payslips = Payslip.objects.filter(
            tenant_id=tenant_id, employee=emp, jurisdiction='CA', payroll_run__year=tax_year
        ).prefetch_related('line_items')
        data = generate_ca_t1_prep(tenant, emp, tax_year, payslips)
        content = json.dumps(data, indent=2).encode('utf-8')
        doc = save_compliance_document(tenant_id, emp, 'CA', 'CA_T1_PREP', tax_year, content, data, ext='json')
        return Response({'document_id': str(doc.id), 'data': data})
