from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from organization.views import BaseTenantViewSet

from .models import SalaryComponent, SalaryStructure, PayrollRun, Payslip
from .serializers import (
    SalaryComponentSerializer,
    SalaryStructureSerializer,
    PayrollRunSerializer,
    PayslipSerializer,
)


class SalaryComponentViewSet(BaseTenantViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer


class SalaryStructureViewSet(BaseTenantViewSet):
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer


class PayrollRunViewSet(BaseTenantViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        run = self.get_object()
        if run.status == 'Locked':
            return Response({'detail': 'Payroll run is locked.'}, status=status.HTTP_400_BAD_REQUEST)

        structures = SalaryStructure.objects.filter(tenant_id=run.tenant_id).select_related('employee')
        created = 0
        for structure in structures:
            monthly_ctc = structure.ctc / Decimal('12')
            gross = monthly_ctc
            deductions = gross * Decimal('0.1')
            net = gross - deductions
            _, was_created = Payslip.objects.get_or_create(
                tenant_id=run.tenant_id,
                payroll_run=run,
                employee=structure.employee,
                defaults={
                    'gross_pay': gross.quantize(Decimal('0.01')),
                    'total_deductions': deductions.quantize(Decimal('0.01')),
                    'net_pay': net.quantize(Decimal('0.01')),
                    'is_released': False,
                },
            )
            if was_created:
                created += 1

        run.status = 'Processing'
        run.processed_by = request.user
        run.save(update_fields=['status', 'processed_by', 'updated_at'])

        return Response({
            'payroll_run': PayrollRunSerializer(run).data,
            'payslips_created': created,
            'payslips_total': Payslip.objects.filter(payroll_run=run).count(),
        })


class PayslipViewSet(BaseTenantViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
