from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from core.tenant_utils import get_employee_for_user
from notifications.services import notify_user
from organization.views import BaseTenantViewSet

from .models import LeaveType, LeavePolicy, LeaveBalance, LeaveRequest
from .serializers import LeaveTypeSerializer, LeavePolicySerializer, LeaveBalanceSerializer, LeaveRequestSerializer


class LeaveTypeViewSet(BaseTenantViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer


class LeavePolicyViewSet(BaseTenantViewSet):
    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer


class LeaveBalanceViewSet(BaseTenantViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer


class LeaveRequestViewSet(BaseTenantViewSet):
    queryset = LeaveRequest.objects.select_related('employee', 'leave_type', 'approved_by').all()
    serializer_class = LeaveRequestSerializer

    @action(detail=False, methods=['post'])
    def apply_leave(self, request):
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response({'detail': 'Employee profile required.'}, status=403)

        leave_type_id = request.data.get('leave_type_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        reason = request.data.get('reason', '')

        if not leave_type_id:
            raise ValidationError({'leave_type_id': 'This field is required.'})

        leave_req = LeaveRequest.objects.create(
            tenant_id=employee.tenant_id,
            employee=employee,
            leave_type_id=leave_type_id,
            start_date=start_date or timezone.now().date(),
            end_date=end_date or timezone.now().date(),
            reason=reason,
            status='Pending',
        )

        mgr = employee.reporting_manager
        if mgr and mgr.user_id:
            notify_user(
                mgr.user_id,
                employee.tenant_id,
                'Leave request',
                f'{employee.first_name} submitted a leave request.',
            )

        return Response(
            {
                'status': 'success',
                'message': 'Leave application submitted successfully',
                'data': LeaveRequestSerializer(leave_req).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave_req = self.get_object()
        approver = get_employee_for_user(request.user)
        leave_req.status = 'Approved'
        leave_req.approved_by = approver
        leave_req.save(update_fields=['status', 'approved_by', 'updated_at'])
        if leave_req.employee.user_id:
            notify_user(
                leave_req.employee.user_id,
                leave_req.tenant_id,
                'Leave approved',
                'Your leave request was approved.',
            )
        return Response(LeaveRequestSerializer(leave_req).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave_req = self.get_object()
        leave_req.status = 'Rejected'
        leave_req.save(update_fields=['status', 'updated_at'])
        reason = request.data.get('reason', 'Your leave request was rejected.')
        if leave_req.employee.user_id:
            notify_user(
                leave_req.employee.user_id,
                leave_req.tenant_id,
                'Leave rejected',
                reason,
            )
        return Response(LeaveRequestSerializer(leave_req).data)
