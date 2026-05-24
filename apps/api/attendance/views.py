from decimal import Decimal

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.tenant_utils import get_employee_for_user, resolve_tenant_id
from notifications.services import notify_user
from organization.views import BaseTenantViewSet

from .models import Shift, GeoFence, AttendanceLog, AttendanceRegularization, AttendanceSettings, FieldLocationPing
from .serializers import (
    ShiftSerializer, GeoFenceSerializer, AttendanceLogSerializer,
    AttendanceRegularizationSerializer, AttendanceSettingsSerializer, FieldLocationPingSerializer,
)
from .services.geofence import validate_punch_location
from .services.office_hours import is_within_office_hours
from .services.rules import resolve_attendance_rules, validate_not_near_home, employee_home_location_complete


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
        if not employee.employee_type_id:
            return Response({'detail': 'Employee type is mandatory. Contact HR.'}, status=403)

        settings = AttendanceSettings.objects.filter(tenant_id=employee.tenant_id).first()
        if settings and not settings.allow_web_punch:
            return Response({'detail': 'Web punch is disabled.'}, status=403)
        rules = resolve_attendance_rules(employee)

        lat = request.data.get('lat') or request.data.get('location_lat')
        lng = request.data.get('lng') or request.data.get('location_lng')
        selfie = request.FILES.get('selfie')

        if rules.require_home_location and not employee_home_location_complete(employee):
            return Response({'detail': 'Please complete your home location in My Profile before punching in.'}, status=422)

        if rules.require_selfie and not selfie:
            return Response({'detail': 'Selfie is required for punch.'}, status=422)

        ok, msg, _, _ = validate_punch_location(
            employee.tenant_id,
            lat,
            lng,
            require_gps=rules.require_gps,
            require_office_geofence=rules.require_office_geofence,
            allow_remote_punch=rules.allow_remote_punch,
        )
        if not ok:
            return Response({'detail': msg}, status=422)
        ok, msg = validate_not_near_home(employee, lat, lng, rules)
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

        payload = AttendanceLogSerializer(log).data
        if is_check_in and rules.enable_live_tracking:
            payload['tracking_active'] = True
            payload['interval_minutes'] = rules.tracking_interval_minutes
        return Response(payload, status=status.HTTP_200_OK)

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


def _user_role_names(user):
    if user.is_superuser:
        return {'Super Admin'}
    return set(user.role_mappings.values_list('role__name', flat=True))


class FieldLocationPingViewSet(BaseTenantViewSet):
    queryset = FieldLocationPing.objects.select_related('employee', 'attendance_log').all()
    serializer_class = FieldLocationPingSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'create':
            employee = get_employee_for_user(self.request.user)
            return qs.filter(employee=employee) if employee else qs.none()
        roles = _user_role_names(self.request.user)
        if roles.intersection({'HR Admin', 'Company Admin', 'Super Admin'}):
            return qs
        employee = get_employee_for_user(self.request.user)
        return qs.filter(employee=employee) if employee else qs.none()

    def create(self, request, *args, **kwargs):
        employee = get_employee_for_user(request.user)
        if not employee:
            raise PermissionDenied('Employee profile required.')
        rules = resolve_attendance_rules(employee)
        if not rules.enable_live_tracking:
            raise ValidationError('Live field tracking is not enabled for your employee type.')
        if not is_within_office_hours(employee.tenant_id):
            raise ValidationError('Location ping rejected outside configured office hours.')

        today = timezone.localdate()
        log = AttendanceLog.objects.filter(
            tenant_id=employee.tenant_id,
            employee=employee,
            date=today,
            check_in__isnull=False,
            check_out__isnull=True,
        ).first()
        if not log:
            raise ValidationError('Active check-in required before sending field location ping.')

        recent = FieldLocationPing.objects.filter(
            tenant_id=employee.tenant_id,
            employee=employee,
        ).order_by('-recorded_at').first()
        if recent:
            elapsed = (timezone.now() - recent.recorded_at).total_seconds()
            if elapsed < (rules.tracking_interval_minutes * 60) - 10:
                raise ValidationError('Please wait for the next tracking interval.')

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ping = ser.save(
            tenant_id=employee.tenant_id,
            employee=employee,
            attendance_log=log,
            is_within_office_hours=True,
            near_home=not validate_not_near_home(employee, ser.validated_data['latitude'], ser.validated_data['longitude'], rules)[0],
        )
        return Response(self.get_serializer(ping).data, status=201)

    @action(detail=False, methods=['get'])
    def live(self, request):
        roles = _user_role_names(request.user)
        if not roles.intersection({'HR Admin', 'Company Admin', 'Super Admin'}):
            raise PermissionDenied('Only HR/Admin roles can view live field tracking.')
        qs = self.get_queryset().order_by('employee_id', '-recorded_at')
        latest = {}
        for ping in qs:
            if ping.employee_id not in latest:
                latest[ping.employee_id] = ping
        rows = []
        now = timezone.now()
        for ping in latest.values():
            rules = resolve_attendance_rules(ping.employee)
            stale_after = rules.tracking_interval_minutes * 120
            rows.append({
                'employee_id': str(ping.employee_id),
                'employee_name': f'{ping.employee.first_name} {ping.employee.last_name}',
                'latitude': ping.latitude,
                'longitude': ping.longitude,
                'recorded_at': ping.recorded_at,
                'status': 'Stale' if (now - ping.recorded_at).total_seconds() > stale_after else 'Active',
                'near_home': ping.near_home,
            })
        return Response(rows)

    @action(detail=False, methods=['get'])
    def trail(self, request):
        roles = _user_role_names(request.user)
        employee = get_employee_for_user(request.user)
        employee_id = request.query_params.get('employee_id') or (str(employee.id) if employee else None)
        if not employee_id:
            raise ValidationError('employee_id is required.')
        if not roles.intersection({'HR Admin', 'Company Admin', 'Super Admin'}):
            if not employee or str(employee.id) != employee_id:
                raise PermissionDenied('Not authorized to view this trail.')
        date = request.query_params.get('date') or str(timezone.localdate())
        qs = self.get_queryset().filter(employee_id=employee_id, recorded_at__date=date).order_by('recorded_at')
        return Response(self.get_serializer(qs, many=True).data)
