import csv
import io
from decimal import Decimal

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedTenantUser

from core.models import Tenant
from core.tenant_utils import attach_tenant_to_request, get_employee_for_user, resolve_request_tenant_id
from organization.views import BaseTenantViewSet

from .models import (
    SalaryComponent,
    SalaryStructure,
    PayrollRun,
    Payslip,
    PayrollLineItem,
    TaxDeclaration,
    TaxAiTipUsage,
)
from .serializers import (
    SalaryComponentSerializer,
    SalaryStructureSerializer,
    PayrollRunSerializer,
    PayslipSerializer,
    PayrollLineItemSerializer,
    TaxDeclarationSerializer,
)
from .services import generate_payslips_for_run
from .tax_ai_credits import can_consume_credit, current_period, get_credit_status
from .tax_ai_service import generate_tax_tips
from compliance.pdf_fill import pdf_from_text


class SalaryComponentViewSet(BaseTenantViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer


class SalaryStructureViewSet(BaseTenantViewSet):
    queryset = SalaryStructure.objects.select_related('employee').all()
    serializer_class = SalaryStructureSerializer


class PayrollRunViewSet(BaseTenantViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        run = self.get_object()
        if run.status in ('Locked', 'Released'):
            return Response({'detail': 'Payroll run is locked or released.'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = Tenant.objects.filter(id=run.tenant_id).first()
        created = generate_payslips_for_run(run, tenant)
        run.status = 'Processing'
        run.processed_by = request.user
        run.save(update_fields=['status', 'processed_by', 'updated_at'])

        return Response({
            'payroll_run': PayrollRunSerializer(run).data,
            'payslips_created': created,
            'payslips_total': run.payslips.count(),
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        run = self.get_object()
        if run.status != 'Processing':
            return Response({'detail': 'Only processing runs can be approved.'}, status=status.HTTP_400_BAD_REQUEST)
        run.status = 'Approved'
        run.save(update_fields=['status', 'updated_at'])
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        run = self.get_object()
        if run.status != 'Approved':
            return Response({'detail': 'Only approved runs can be locked.'}, status=status.HTTP_400_BAD_REQUEST)
        run.status = 'Locked'
        run.save(update_fields=['status', 'updated_at'])
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        run = self.get_object()
        if run.status != 'Locked':
            return Response({'detail': 'Only locked runs can be released.'}, status=status.HTTP_400_BAD_REQUEST)
        run.payslips.update(is_released=True)
        run.status = 'Released'
        run.save(update_fields=['status', 'updated_at'])
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['get'])
    def bank_export(self, request, pk=None):
        run = self.get_object()
        payslips = run.payslips.select_related('employee').prefetch_related('employee__bank_details')
        output = io.StringIO()
        writer = csv.writer(output)
        if run.jurisdiction == 'IN':
            writer.writerow(['Employee', 'Account', 'IFSC', 'Amount', 'Currency'])
            for ps in payslips:
                bank = getattr(ps.employee, 'bank_details', None)
                writer.writerow([
                    f'{ps.employee.first_name} {ps.employee.last_name}',
                    bank.account_number if bank else '',
                    bank.ifsc_code if bank else '',
                    ps.net_pay,
                    ps.currency,
                ])
        elif run.jurisdiction == 'US':
            writer.writerow(['Employee', 'Account', 'Routing', 'Amount', 'Currency'])
            for ps in payslips:
                bank = getattr(ps.employee, 'bank_details', None)
                writer.writerow([
                    f'{ps.employee.first_name} {ps.employee.last_name}',
                    bank.account_number if bank else '',
                    bank.ifsc_code if bank else '',
                    ps.net_pay,
                    ps.currency,
                ])
        else:
            writer.writerow(['Employee', 'Account', 'Transit', 'Amount', 'Currency'])
            for ps in payslips:
                bank = getattr(ps.employee, 'bank_details', None)
                writer.writerow([
                    f'{ps.employee.first_name} {ps.employee.last_name}',
                    bank.account_number if bank else '',
                    bank.ifsc_code if bank else '',
                    ps.net_pay,
                    ps.currency,
                ])
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bank_{run.jurisdiction}_{run.year}_{run.month}.csv"'
        return response


class PayslipViewSet(BaseTenantViewSet):
    queryset = Payslip.objects.select_related('payroll_run', 'employee').prefetch_related('line_items')
    serializer_class = PayslipSerializer

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        payslip = self.get_object()
        lines = [
            f'Employee: {payslip.employee.first_name} {payslip.employee.last_name}',
            f'Period: {payslip.payroll_run.month}/{payslip.payroll_run.year}',
            f'Jurisdiction: {payslip.jurisdiction}',
            f'Gross: {payslip.currency} {payslip.gross_pay}',
            f'Deductions: {payslip.currency} {payslip.total_deductions}',
            f'Net Pay: {payslip.currency} {payslip.net_pay}',
            '',
            'Line Items:',
        ]
        for li in payslip.line_items.all():
            prefix = '[ER] ' if li.is_employer_contribution else ''
            lines.append(f'  {prefix}{li.name}: {payslip.currency} {li.amount}')
        pdf_bytes = pdf_from_text('Payslip', lines)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payslip_{payslip.id}.pdf"'
        return response


class PayrollLineItemViewSet(BaseTenantViewSet):
    queryset = PayrollLineItem.objects.all()
    serializer_class = PayrollLineItemSerializer


class TaxDeclarationViewSet(BaseTenantViewSet):
    queryset = TaxDeclaration.objects.all()
    serializer_class = TaxDeclarationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        jurisdiction = self.request.query_params.get('jurisdiction')
        employee_id = self.request.query_params.get('employee')
        if jurisdiction:
            qs = qs.filter(jurisdiction=jurisdiction)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        employee = get_employee_for_user(self.request.user)
        if employee and not employee_id:
            qs = qs.filter(employee=employee)
        return qs

    def perform_create(self, serializer):
        tenant_id = resolve_request_tenant_id(self.request)
        if not tenant_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('No tenant assigned to your account.')
        extra = {'tenant_id': tenant_id}
        employee = get_employee_for_user(self.request.user)
        if employee and not serializer.validated_data.get('employee'):
            extra['employee'] = employee
        serializer.save(**extra)


class TaxAiTipsViewSet(viewsets.ViewSet):
    """ESS AI tax savings tips — 3 credits per employee per calendar month."""

    permission_classes = [IsAuthenticatedTenantUser]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        attach_tenant_to_request(request)

    def _require_employee(self, request):
        employee = get_employee_for_user(request.user)
        if not employee:
            return None, Response(
                {'detail': 'No employee profile linked to this account.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return employee, None

    @action(detail=False, methods=['get'], url_path='credits')
    def credits(self, request):
        employee, err = self._require_employee(request)
        if err:
            return err
        return Response(get_credit_status(employee))

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        employee, err = self._require_employee(request)
        if err:
            return err

        jurisdiction = request.data.get('jurisdiction')
        fiscal_year = request.data.get('fiscal_year')
        if not jurisdiction or fiscal_year is None:
            return Response(
                {'detail': 'jurisdiction and fiscal_year are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fiscal_year = int(fiscal_year)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'fiscal_year must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not can_consume_credit(employee):
            status_data = get_credit_status(employee)
            return Response(
                {
                    'detail': f'Monthly limit of {status_data["limit"]} AI tax tip requests reached.',
                    **status_data,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            tips = generate_tax_tips(employee, jurisdiction, fiscal_year)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        tenant_id = resolve_request_tenant_id(request)
        TaxAiTipUsage.objects.create(
            tenant_id=tenant_id,
            employee=employee,
            period=current_period(),
            jurisdiction=jurisdiction,
            fiscal_year=fiscal_year,
            response_snapshot=tips,
        )

        credit_status = get_credit_status(employee)
        return Response({**tips, **credit_status})


class PayrollSettingsViewSet(viewsets.ViewSet):
    """Tenant payroll policy (variable pay, jurisdictions)."""

    permission_classes = [IsAuthenticatedTenantUser]

    def list(self, request):
        tenant = request.user.tenant
        if not tenant:
            return Response({'detail': 'No tenant.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'enabled_jurisdictions': tenant.enabled_jurisdictions,
            'default_currency': tenant.default_currency,
            'fiscal_year_start_month': tenant.fiscal_year_start_month,
            'variable_pay_enabled': tenant.variable_pay_enabled,
            'allow_employee_variable_override': tenant.allow_employee_variable_override,
        })

    def partial_update(self, request):
        tenant = request.user.tenant
        if not tenant:
            return Response({'detail': 'No tenant.'}, status=status.HTTP_400_BAD_REQUEST)
        for field in (
            'enabled_jurisdictions',
            'variable_pay_enabled',
            'allow_employee_variable_override',
            'fiscal_year_start_month',
        ):
            if field in request.data:
                setattr(tenant, field, request.data[field])
        tenant.save()
        return self.list(request)
