import hashlib

from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import AuthSession, User
from wfh.tracker_auth import (
    exchange_access_for_tracker_session,
    issue_tracker_session,
    refresh_tracker_session,
    revoke_tracker_session,
)
from core.gcm_crypto import ALGORITHM, is_gcm_blob
from core.storage import TrackerStorageService
from wfh.tracker_auth import latest_tracker_key_wrapped
from wfh.models import (
    EmployeeConsent,
    IdleLog,
    ScreenshotCapture,
    TrackerDevice,
    WFHPolicy,
    WorkSession,
    WorkSessionEvent,
    WorkSessionFocusEvent,
    WorkSessionHeartbeat,
)
from wfh.permissions import HasActiveApprovedWFH, HasActiveWorkSession, HasRecordedConsent, IsEmployeeUser
from wfh.serializers import (
    EmployeeConsentSerializer,
    IdleLogSerializer,
    SessionReportSerializer,
    TrackerDeviceSerializer,
    WFHPolicySerializer,
    WFHRequestSerializer,
    WorkSessionSerializer,
    TrackerBugReportSerializer,
    WorkSessionHistorySerializer,
)
from wfh.services.report import persist_session_report
from wfh.services.productivity import classify_focus
from wfh.services.session import finalize_session, get_active_session, get_approved_wfh_for_today
from wfh.utils import audit_log, get_client_ip, get_employee_for_user


class TrackerBrowserLoginPageView(View):
    """HTML login page for desktop tracker browser SSO (no Next.js required)."""

    def get(self, request):
        from wfh.browser_login import _allowed_redirect, render_browser_login_page

        if not _allowed_redirect(request.GET.get("tracker_redirect", "")):
            return HttpResponseBadRequest("Invalid or missing tracker_redirect parameter.")
        api_base = request.build_absolute_uri("/api/v1").rstrip("/")
        html = render_browser_login_page(request, api_base)
        return HttpResponse(html, content_type="text/html; charset=utf-8")


class TrackerLoginThrottle(AnonRateThrottle):
    rate = "10/min"


class ScreenshotUploadThrottle(UserRateThrottle):
    scope = "tracker_screenshot"


class TrackerLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [TrackerLoginThrottle]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)
        auth_user = authenticate(username=user.username, password=password)
        if not auth_user:
            return Response({"error": "Invalid credentials"}, status=401)
        employee = get_employee_for_user(auth_user)
        if not employee:
            return Response(
                {
                    "error": "Employee profile not found.",
                    "detail": (
                        "Your login is valid but no Employee record is linked to this user. "
                        "Ask HR to link your profile, or run: python manage.py seed_wfh"
                    ),
                },
                status=403,
            )
        tokens = issue_tracker_session(auth_user, request=request)
        policy = WFHPolicy.get_active(employee.tenant_id)
        audit_log(request, "tracker.login", "User", auth_user.id)
        return Response(
            {
                **tokens,
                "email": auth_user.email,
                "employee": {
                    "id": str(employee.id),
                    "name": f"{employee.first_name} {employee.last_name}",
                },
                "policy": WFHPolicySerializer(policy).data if policy else None,
            }
        )


class TrackerSessionExchangeView(APIView):
    """Exchange browser/web access token for a tracker-only session (7-day refresh)."""

    permission_classes = [AllowAny]
    throttle_classes = [TrackerLoginThrottle]

    def post(self, request):
        access = request.data.get("access_token")
        if not access:
            return Response({"error": "access_token required"}, status=400)
        try:
            tokens = exchange_access_for_tracker_session(access, request=request)
        except Exception as e:
            return Response({"error": str(e)}, status=401)
        from rest_framework_simplejwt.tokens import AccessToken

        user_id = AccessToken(access).get("user_id")
        user = User.objects.filter(pk=user_id).first()
        employee = get_employee_for_user(user) if user else None
        if not employee:
            return Response({"error": "Employee profile not found."}, status=403)
        policy = WFHPolicy.get_active(employee.tenant_id)
        return Response(
            {
                **tokens,
                "email": user.email,
                "employee": {
                    "id": str(employee.id),
                    "name": f"{employee.first_name} {employee.last_name}",
                },
                "policy": WFHPolicySerializer(policy).data if policy else None,
            }
        )


class TrackerRefreshView(APIView):
    """Refresh tracker access token — not affected by web logout."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh = request.data.get("refresh_token")
        if not refresh:
            return Response({"error": "refresh_token required"}, status=400)
        try:
            tokens = refresh_tracker_session(refresh)
            return Response(tokens)
        except Exception as e:
            return Response({"error": str(e)}, status=401)


class TrackerLogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh = request.data.get("refresh_token")
        if refresh:
            revoke_tracker_session(refresh)
        if request.user.is_authenticated:
            audit_log(request, "tracker.logout", "User", request.user.id)
        return Response({"status": "ok"})


class TrackerProfileView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        policy = WFHPolicy.get_active(employee.tenant_id)
        consent = EmployeeConsent.objects.filter(
            employee=employee, consent_type="wfh_tracking_v1", revoked_at__isnull=True
        ).exists()
        return Response(
            {
                "employee_id": str(employee.id),
                "name": f"{employee.first_name} {employee.last_name}",
                "has_consent": consent,
                "policy": WFHPolicySerializer(policy).data if policy else None,
            }
        )


class TrackerAuthBootstrapView(APIView):
    """Post browser SSO: validate employee profile and return tracker context."""

    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response(
                {"detail": "Employee profile not found. Contact HR to link your account."},
                status=403,
            )
        policy = WFHPolicy.get_active(employee.tenant_id)
        return Response(
            {
                "employee": {
                    "id": str(employee.id),
                    "name": f"{employee.first_name} {employee.last_name}",
                },
                "policy": WFHPolicySerializer(policy).data if policy else None,
            }
        )


class ApprovedWFHStatusView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        wfh = get_approved_wfh_for_today(employee)
        session = get_active_session(employee)
        return Response(
            {
                "can_track": wfh is not None,
                "message": "Approved WFH found." if wfh else "No approved WFH for today.",
                "wfh_request": WFHRequestSerializer(wfh).data if wfh else None,
                "active_session": WorkSessionSerializer(session).data if session else None,
            }
        )


class TrackerConsentView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        consent = EmployeeConsent.objects.create(
            tenant=employee.tenant,
            employee=employee,
            consent_type=request.data.get("consent_type", "wfh_tracking_v1"),
            ip_address=get_client_ip(request),
            app_version=request.data.get("app_version", ""),
        )
        audit_log(request, "tracker.consent", "EmployeeConsent", consent.id)
        return Response(EmployeeConsentSerializer(consent).data, status=201)


class DeviceRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        device_uuid = request.data.get("device_uuid")
        if not device_uuid:
            return Response({"detail": "device_uuid required"}, status=400)
        device, _ = TrackerDevice.objects.update_or_create(
            tenant=employee.tenant,
            device_uuid=device_uuid,
            defaults={
                "employee": employee,
                "device_name": request.data.get("device_name", ""),
                "os_name": request.data.get("os_name", ""),
                "os_version": request.data.get("os_version", ""),
                "mac_address_hash": request.data.get("mac_address_hash", ""),
                "app_version": request.data.get("app_version", ""),
                "last_seen_at": timezone.now(),
            },
        )
        audit_log(request, "tracker.device.register", "TrackerDevice", device.id)
        return Response(TrackerDeviceSerializer(device).data)


class DeviceStatusView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        devices = TrackerDevice.objects.filter(employee=employee)
        return Response(TrackerDeviceSerializer(devices, many=True).data)


class SessionStartView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser, HasActiveApprovedWFH, HasRecordedConsent]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        if get_active_session(employee):
            return Response({"detail": "Session already active."}, status=400)
        wfh = get_approved_wfh_for_today(employee)
        task_title = (request.data.get("task_title") or "").strip()
        task_description = (request.data.get("task_description") or "").strip()
        if not task_title:
            return Response({"detail": "task_title is required."}, status=400)
        if not task_description:
            return Response({"detail": "task_description is required."}, status=400)
        device_uuid = request.data.get("device_uuid")
        device = TrackerDevice.objects.filter(tenant=employee.tenant, device_uuid=device_uuid).first()
        session = WorkSession.objects.create(
            tenant=employee.tenant,
            employee=employee,
            wfh_request=wfh,
            device=device,
            start_time=timezone.now(),
            status=WorkSession.STATUS_ACTIVE,
            task_title=task_title[:255],
            task_description=task_description,
            encryption_key_wrapped=latest_tracker_key_wrapped(request.user),
        )
        audit_log(request, "tracker.session.start", "WorkSession", session.id)
        WorkSessionEvent.objects.create(
            tenant=employee.tenant,
            session=session,
            employee=employee,
            event_type=WorkSessionEvent.EVENT_SESSION_START,
            occurred_at=session.start_time,
            detail=task_title,
            metadata={"task_description": task_description},
        )
        return Response(WorkSessionSerializer(session).data, status=201)


def _record_session_event(session, employee, event_type, detail="", metadata=None):
    WorkSessionEvent.objects.create(
        tenant=session.tenant,
        session=session,
        employee=employee,
        event_type=event_type,
        occurred_at=timezone.now(),
        detail=detail[:512],
        metadata=metadata or {},
    )


class SessionPauseView(APIView):
    permission_classes = [IsAuthenticated, HasActiveWorkSession]

    def post(self, request):
        session = get_active_session(get_employee_for_user(request.user))
        policy = WFHPolicy.get_active(session.tenant_id)
        if policy and not policy.allow_pause:
            return Response({"detail": "Pause not allowed by policy."}, status=403)
        session.status = WorkSession.STATUS_PAUSED
        session.save(update_fields=["status", "updated_at"])
        reason = request.data.get("reason", "manual")
        et = (
            WorkSessionEvent.EVENT_AUTO_PAUSE
            if reason == "auto_idle"
            else WorkSessionEvent.EVENT_PAUSE
        )
        _record_session_event(session, session.employee, et, detail=reason)
        audit_log(request, "tracker.session.pause", "WorkSession", session.id)
        return Response(WorkSessionSerializer(session).data)


class SessionResumeView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        session = WorkSession.objects.filter(
            employee=employee, status=WorkSession.STATUS_PAUSED
        ).first()
        if not session:
            return Response({"detail": "No paused session."}, status=404)
        session.status = WorkSession.STATUS_ACTIVE
        session.save(update_fields=["status", "updated_at"])
        _record_session_event(session, employee, WorkSessionEvent.EVENT_RESUME, detail=request.data.get("reason", ""))
        audit_log(request, "tracker.session.resume", "WorkSession", session.id)
        return Response(WorkSessionSerializer(session).data)


class SessionReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        session = WorkSession.objects.filter(
            employee=employee,
            status__in=[WorkSession.STATUS_ACTIVE, WorkSession.STATUS_PAUSED],
        ).first()
        if not session:
            return Response({"detail": "No active session for report."}, status=404)
        ser = SessionReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        persist_session_report(session, employee, ser.validated_data)
        audit_log(request, "tracker.session.report", "WorkSession", session.id)
        return Response({"status": "ok", "session_id": str(session.id)})


class SessionStopView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        session = WorkSession.objects.filter(
            employee=employee, status__in=[WorkSession.STATUS_ACTIVE, WorkSession.STATUS_PAUSED]
        ).first()
        if not session:
            return Response({"detail": "No active session."}, status=404)
        report = request.data.get("report")
        if report:
            ser = SessionReportSerializer(data=report)
            ser.is_valid(raise_exception=True)
            persist_session_report(session, employee, ser.validated_data)
        session.status = WorkSession.STATUS_STOPPED
        finalize_session(session)
        audit_log(request, "tracker.session.stop", "WorkSession", session.id)
        return Response(WorkSessionSerializer(session).data)


class SessionCurrentView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        session = get_active_session(employee)
        if not session:
            return Response({"session": None})
        return Response({"session": WorkSessionSerializer(session).data})


class SessionHeartbeatView(APIView):
    permission_classes = [IsAuthenticated, HasActiveWorkSession]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        session = get_active_session(employee)
        device = session.device
        hb = WorkSessionHeartbeat.objects.create(
            tenant=session.tenant,
            session=session,
            employee=employee,
            device=device,
            heartbeat_at=timezone.now(),
            app_status=request.data.get("app_status", "active"),
            battery_status=request.data.get("battery_status", ""),
            network_status=request.data.get("network_status", "online"),
        )
        if device:
            device.last_seen_at = timezone.now()
            device.save(update_fields=["last_seen_at"])
        return Response({"id": str(hb.id), "heartbeat_at": hb.heartbeat_at})


class ScreenshotUploadView(APIView):
    permission_classes = [IsAuthenticated, HasActiveWorkSession]
    throttle_classes = [ScreenshotUploadThrottle]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        session = get_active_session(employee)
        if session.status != WorkSession.STATUS_ACTIVE:
            return Response({"detail": "Screenshots only while session is active (not paused)."}, status=403)
        checksum = request.data.get("checksum") or request.POST.get("checksum") or request.query_params.get("checksum")
        uploaded = request.FILES.get("file")
        if not uploaded or not checksum:
            return Response({"detail": "file and checksum required"}, status=400)
        if ScreenshotCapture.objects.filter(session=session, checksum_sha256=checksum).exists():
            existing = ScreenshotCapture.objects.get(session=session, checksum_sha256=checksum)
            return Response({"id": str(existing.id), "status": "duplicate"})
        gcm_blob = uploaded.read()
        if not is_gcm_blob(gcm_blob):
            return Response(
                {"detail": "Screenshot must be AES-256-GCM encrypted (invalid payload)."},
                status=400,
            )
        monitor = int(request.data.get("monitor_number", 1))
        storage_key = TrackerStorageService.save_gcm_screenshot(
            employee.tenant_id,
            employee.id,
            session.id,
            gcm_blob,
            checksum,
        )
        cap = ScreenshotCapture.objects.create(
            tenant=employee.tenant,
            session=session,
            employee=employee,
            captured_at=timezone.now(),
            storage_key=storage_key,
            monitor_number=monitor,
            file_size=len(gcm_blob),
            checksum_sha256=checksum,
            encrypted=True,
            encryption_algorithm=ALGORITHM,
            window_title=request.data.get("window_title", "")[:512],
        )
        app_name = (request.data.get("application_name") or "").strip()[:255]
        tab_title = (request.data.get("active_tab_title") or "").strip()[:512]
        focus_seconds = int(request.data.get("app_focus_seconds", 0) or 0)
        is_productive, matched_rule = classify_focus(
            tenant_id=employee.tenant_id,
            app_name=app_name,
            tab_title=tab_title,
        )
        WorkSessionFocusEvent.objects.create(
            tenant=employee.tenant,
            session=session,
            employee=employee,
            occurred_at=timezone.now(),
            application_name=app_name,
            active_tab_title=tab_title,
            window_title=cap.window_title,
            focus_seconds=max(0, focus_seconds),
            is_productive=is_productive,
            matched_rule=matched_rule,
            screenshot=cap,
        )
        WorkSession.objects.filter(pk=session.pk).update(
            screenshot_count=session.screenshot_count + 1
        )
        audit_log(request, "tracker.screenshot.upload", "ScreenshotCapture", cap.id)
        return Response({"id": str(cap.id)}, status=201)


class IdleLogCreateView(APIView):
    permission_classes = [IsAuthenticated, HasActiveWorkSession]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        session = get_active_session(employee)
        ser = IdleLogSerializer(data={**request.data, "session": str(session.id), "employee": str(employee.id)})
        ser.is_valid(raise_exception=True)
        log = IdleLog.objects.create(tenant=employee.tenant, **ser.validated_data)
        duration = log.idle_duration or 0
        session.idle_duration += duration
        session.active_duration = max(0, session.total_duration - session.idle_duration)
        session.save(update_fields=["idle_duration", "active_duration", "updated_at"])
        return Response(IdleLogSerializer(log).data, status=201)


class SessionHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        # Get past 30 days of sessions
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        sessions = WorkSession.objects.filter(
            employee=employee,
            start_time__gte=thirty_days_ago
        ).order_by("-start_time")
        
        return Response(WorkSessionHistorySerializer(sessions, many=True).data)


class BugReportCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmployeeUser]

    def post(self, request):
        employee = get_employee_for_user(request.user)
        # The desktop app will send base64 or a file upload, but for now we accept text payload
        # Actually since screenshots are optional, we can just save it.
        # If they send an image, we should ideally upload it to S3, but for now just save the report text.
        ser = TrackerBugReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        report = ser.save(tenant=employee.tenant, employee=employee)
        return Response(TrackerBugReportSerializer(report).data, status=201)

