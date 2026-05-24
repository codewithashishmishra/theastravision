from decimal import Decimal

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.tenant_utils import get_employee_for_user, resolve_tenant_id
from notifications.services import notify_user
from organization.views import BaseTenantViewSet

from .models import Shift, GeoFence, AttendanceLog, AttendanceRegularization, AttendanceSettings
from .serializers import (
    ShiftSerializer, GeoFenceSerializer, AttendanceLogSerializer,
    AttendanceRegularizationSerializer, AttendanceSettingsSerializer,
)
from .services.geofence import validate_punch_location


class AttendanceSettingsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response({'detail': 'No tenant.'}, status=403)
        obj, _ = AttendanceSettings.objects.get_or_create(tenant_id=tenant_id)
        return Response(AttendanceSettingsSerializer(obj).data)

    def put(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response({'detail': 'No tenant.'}, status=403)
        obj, _ = AttendanceSettings.objects.get_or_create(tenant_id=tenant_id)
        ser = AttendanceSettingsSerializer(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class ShiftViewSet(BaseTenantViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer


class GeoFenceViewSet(BaseTenantViewSet):
    queryset = GeoFence.objects.all()
    serializer_class = GeoFenceSerializer


class AttendanceLogViewSet(BaseTenantViewSet):
    queryset = AttendanceLog.objects.select_related('employee').all()
    serializer_class = AttendanceLogSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        employee = get_employee_for_user(self.request.user)
        mine = self.request.query_params.get('mine')
        if mine and employee:
            return qs.filter(employee=employee)
        return qs

    def _punch(self, request, is_check_in):
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response({'detail': 'Employee profile required.'}, status=403)

        settings = AttendanceSettings.objects.filter(tenant_id=employee.tenant_id).first()
        if settings and not settings.allow_web_punch:
            return Response({'detail': 'Web punch is disabled.'}, status=403)

        lat = request.data.get('lat') or request.data.get('location_lat')
        lng = request.data.get('lng') or request.data.get('location_lng')
        selfie = request.FILES.get('selfie')

        if settings and settings.require_selfie and not selfie:
            return Response({'detail': 'Selfie is required for punch.'}, status=422)

        ok, msg, _, _ = validate_punch_location(employee.tenant_id, lat, lng)
        if not ok:
            return Response({'detail': msg}, status=422)

        today = timezone.localdate()
        log, _ = AttendanceLog.objects.get_or_create(
            tenant_id=employee.tenant_id,
            employee=employee,
            date=today,
            defaults={'status': 'Present', 'method': 'GPS', 'punch_source': 'Web'},
        )

        now = timezone.now()
        if is_check_in:
            if log.check_in:
                return Response({'detail': 'Already checked in today.'}, status=400)
            log.check_in = now
        else:
            if not log.check_in:
                return Response({'detail': 'Check in first.'}, status=400)
            if log.check_out:
                return Response({'detail': 'Already checked out today.'}, status=400)
            log.check_out = now

        if lat is not None:
            log.location_lat = Decimal(str(lat)) if lat else None
        if lng is not None:
            log.location_lng = Decimal(str(lng)) if lng else None
        if selfie:
            log.selfie = selfie
        log.method = 'GPS' if lat else 'Web'
        log.save()

        return Response(AttendanceLogSerializer(log).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def punch_in(self, request):
        return self._punch(request, True)

    @action(detail=False, methods=['post'])
    def punch_out(self, request):
        return self._punch(request, False)

    @action(detail=False, methods=['post'], url_path='web_punch')
    def web_punch(self, request):
        """Legacy alias — routes to punch_in or punch_out based on type."""
        punch_type = request.data.get('type', 'Check In')
        if punch_type == 'Check Out':
            return self.punch_out(request)
        return self.punch_in(request)


class AttendanceRegularizationViewSet(BaseTenantViewSet):
    queryset = AttendanceRegularization.objects.select_related('employee', 'approved_by').all()
    serializer_class = AttendanceRegularizationSerializer

    def perform_create(self, serializer):
        employee = get_employee_for_user(self.request.user)
        if not employee:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Employee profile required.')
        description = self.request.data.get('description', '')
        reason = self.request.data.get('reason', description)
        serializer.save(
            tenant_id=employee.tenant_id,
            employee=employee,
            reason=reason,
            description=description or reason,
        )
        mgr = employee.reporting_manager
        if mgr and mgr.user_id:
            notify_user(
                mgr.user_id,
                employee.tenant_id,
                'Attendance regularization',
                f'{employee.first_name} submitted a regularization request.',
            )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        reg = self.get_object()
        approver = get_employee_for_user(request.user)
        reg.status = 'Approved'
        reg.approved_by = approver
        reg.approved_at = timezone.now()
        reg.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        if reg.attendance_log and reg.requested_check_in:
            reg.attendance_log.check_in = reg.requested_check_in
        if reg.attendance_log and reg.requested_check_out:
            reg.attendance_log.check_out = reg.requested_check_out
        if reg.attendance_log:
            reg.attendance_log.save()
        if reg.employee.user_id:
            notify_user(
                reg.employee.user_id,
                reg.tenant_id,
                'Regularization approved',
                'Your attendance regularization was approved.',
            )
        return Response(AttendanceRegularizationSerializer(reg).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        reg = self.get_object()
        reg.status = 'Rejected'
        reg.rejection_reason = request.data.get('reason', '')
        reg.save(update_fields=['status', 'rejection_reason', 'updated_at'])
        if reg.employee.user_id:
            notify_user(
                reg.employee.user_id,
                reg.tenant_id,
                'Regularization rejected',
                reg.rejection_reason or 'Your request was rejected.',
            )
        return Response(AttendanceRegularizationSerializer(reg).data)
