from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import require_permission
from core.storage import TrackerStorageService
from employees.models import Employee
from wfh.models import (
    ActivitySummary,
    ProductivityRule,
    ScreenshotCapture,
    TrackerAuditLog,
    TrackerDevice,
    WFHPolicy,
    WFHRequest,
    WorkSession,
    WorkSessionFocusEvent,
)
from wfh.permissions import CanViewEmployeeTracking
from wfh.serializers import (
    ActivitySummarySerializer,
    ScreenshotCaptureSerializer,
    TrackerAuditLogSerializer,
    TrackerAppVersionSerializer,
    ProductivityRuleSerializer,
    TrackerDeviceSerializer,
    WFHPolicySerializer,
    WFHRequestCreateSerializer,
    WFHRequestSerializer,
    WorkSessionSerializer,
    WorkSessionFocusEventSerializer,
)
from wfh.services import cancel_request, hr_approve, manager_approve, reject_request
from wfh.services.notifications import notify_wfh_event
from wfh.services.session import get_active_session
from wfh.utils import (
    audit_log,
    get_employee_for_user,
    is_hr_wfh_viewer,
    resolve_tenant_id,
    user_has_wfh_permission,
)


class WFHRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response({"detail": "Employee profile required."}, status=403)
        qs = WFHRequest.objects.filter(employee=employee).order_by("-created_at")
        return Response(WFHRequestSerializer(qs, many=True).data)

    def post(self, request):
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response({"detail": "Employee profile required."}, status=403)
        ser = WFHRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        wfh = WFHRequest.objects.create(
            tenant=employee.tenant,
            employee=employee,
            **ser.validated_data,
        )
        notify_wfh_event(wfh, "submitted")
        audit_log(request, "wfh.request.create", "WFHRequest", wfh.id)
        return Response(WFHRequestSerializer(wfh).data, status=201)


class WFHRequestTenantListView(APIView):
    """All WFH requests in the user's tenant (HR / view-all)."""

    permission_classes = [IsAuthenticated, require_permission("wfh.view.all", "wfh.approve.hr")]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response(
                {"detail": "No tenant assigned to your account. Contact an administrator."},
                status=403,
            )
        qs = WFHRequest.objects.filter(tenant_id=tenant_id).order_by("-created_at")[:200]
        return Response(WFHRequestSerializer(qs, many=True).data)


class WFHPendingApprovalsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response(
                {"detail": "No tenant assigned to your account. Contact an administrator."},
                status=403,
            )
        qs = WFHRequest.objects.filter(tenant_id=tenant_id)
        if is_hr_wfh_viewer(request.user) or request.user.is_superuser:
            qs = qs.filter(
                status__in=[WFHRequest.STATUS_PENDING, WFHRequest.STATUS_MANAGER_APPROVED]
            )
        else:
            employee = get_employee_for_user(request.user)
            if not employee:
                return Response(
                    {"detail": "Employee profile required for manager approvals."},
                    status=403,
                )
            reportee_ids = Employee.objects.filter(reporting_manager=employee).values_list(
                "id", flat=True
            )
            qs = qs.filter(
                Q(employee_id__in=reportee_ids, status=WFHRequest.STATUS_PENDING)
                | Q(status=WFHRequest.STATUS_MANAGER_APPROVED)
            )
        return Response(WFHRequestSerializer(qs.order_by("-created_at")[:100], many=True).data)


class WFHManagerApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        wfh = WFHRequest.objects.filter(pk=pk).first()
        if not wfh:
            return Response(status=404)
        manager_approve(wfh, request.user, request.data.get("remarks", ""))
        audit_log(request, "wfh.manager_approve", "WFHRequest", wfh.id)
        return Response(WFHRequestSerializer(wfh).data)


class WFHHRApproveView(APIView):
    permission_classes = [IsAuthenticated, require_permission("wfh.approve.hr")]

    def post(self, request, pk):
        wfh = WFHRequest.objects.filter(pk=pk).first()
        if not wfh:
            return Response(status=404)
        hr_approve(wfh, request.user, request.data.get("remarks", ""))
        audit_log(request, "wfh.hr_approve", "WFHRequest", wfh.id)
        return Response(WFHRequestSerializer(wfh).data)


class WFHRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        wfh = WFHRequest.objects.filter(pk=pk).first()
        if not wfh:
            return Response(status=404)
        reject_request(wfh, request.user, request.data.get("remarks", ""))
        audit_log(request, "wfh.reject", "WFHRequest", wfh.id)
        return Response(WFHRequestSerializer(wfh).data)


class WFHCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        wfh = WFHRequest.objects.filter(pk=pk).first()
        if not wfh:
            return Response(status=404)
        employee = get_employee_for_user(request.user)
        if employee and wfh.employee_id != employee.id:
            return Response({"detail": "Not allowed."}, status=403)
        cancel_request(wfh, request.user, request.data.get("remarks", ""))
        return Response(WFHRequestSerializer(wfh).data)


class WFHPolicyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response({"detail": "No tenant assigned to your account."}, status=403)
        policy, _ = WFHPolicy.objects.get_or_create(
            tenant_id=tenant_id,
            defaults={
                "is_active": True,
                "require_hr_approval": True,
                "screenshot_interval_seconds": 15,
                "idle_threshold_seconds": 300,
                "screenshot_retention_days": 30,
            },
        )
        return Response(WFHPolicySerializer(policy).data)

    def put(self, request):
        if not user_has_wfh_permission(request.user, "wfh.policy.manage", "wfh.admin.settings"):
            return Response({"detail": "Permission denied."}, status=403)
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response({"detail": "No tenant assigned to your account."}, status=403)
        policy, _ = WFHPolicy.objects.get_or_create(tenant_id=tenant_id, defaults={"is_active": True})
        ser = WFHPolicySerializer(policy, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class WFHDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response(
                {
                    "approved_wfh_today": 0,
                    "active_sessions": 0,
                    "pending_approvals": 0,
                }
            )
        today = timezone.localdate()
        approved = WFHRequest.objects.filter(
            tenant_id=tenant_id,
            start_date__lte=today,
            end_date__gte=today,
        ).exclude(status__in=[WFHRequest.STATUS_REJECTED, WFHRequest.STATUS_CANCELLED])
        approved_count = sum(1 for r in approved if r.is_wfh_approved)
        active_sessions = WorkSession.objects.filter(
            tenant_id=tenant_id, status=WorkSession.STATUS_ACTIVE
        ).count()
        return Response(
            {
                "approved_wfh_today": approved_count,
                "active_sessions": active_sessions,
                "pending_approvals": WFHRequest.objects.filter(
                    tenant_id=tenant_id, status=WFHRequest.STATUS_PENDING
                ).count(),
            }
        )


class WFHEmployeeSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response([])
        summaries = ActivitySummary.objects.filter(tenant_id=tenant_id).order_by("-summary_date")[:50]
        return Response(ActivitySummarySerializer(summaries, many=True).data)


class WFHTeamSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee_for_user(request.user)
        if not employee:
            return Response([])
        reportees = Employee.objects.filter(reporting_manager=employee)
        data = []
        for rep in reportees:
            session = get_active_session(rep)
            data.append(
                {
                    "employee_id": str(rep.id),
                    "name": f"{rep.first_name} {rep.last_name}",
                    "online": session is not None and session.status == WorkSession.STATUS_ACTIVE,
                    "session_status": session.status if session else None,
                }
            )
        return Response(data)


class WFHSessionReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response(
                {"detail": "No tenant assigned to your account. Contact an administrator."},
                status=403,
            )
        sessions = (
            WorkSession.objects.filter(tenant_id=tenant_id)
            .select_related("employee")
            .order_by("-start_time")[:100]
        )
        return Response(WorkSessionSerializer(sessions, many=True).data)


class WFHProductivityReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response([])
        qs = (
            ActivitySummary.objects.filter(tenant_id=tenant_id)
            .values("summary_date")
            .annotate(
                total_active=Sum("active_seconds"),
                total_idle=Sum("idle_seconds"),
                total_screenshots=Sum("screenshot_count"),
            )
            .order_by("-summary_date")[:30]
        )
        return Response(list(qs))


class ProductivityRuleListCreateView(APIView):
    permission_classes = [IsAuthenticated, require_permission("wfh.policy.manage", "wfh.admin.settings")]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response([])
        rules = ProductivityRule.objects.filter(tenant_id=tenant_id).order_by("name")
        return Response(ProductivityRuleSerializer(rules, many=True).data)

    def post(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response({"detail": "No tenant assigned to your account."}, status=403)
        ser = ProductivityRuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        rule = ser.save(tenant_id=tenant_id)
        return Response(ProductivityRuleSerializer(rule).data, status=201)


class ProductivityRuleDetailView(APIView):
    permission_classes = [IsAuthenticated, require_permission("wfh.policy.manage", "wfh.admin.settings")]

    def put(self, request, pk):
        tenant_id = resolve_tenant_id(request.user)
        rule = ProductivityRule.objects.filter(tenant_id=tenant_id, pk=pk).first()
        if not rule:
            return Response(status=404)
        ser = ProductivityRuleSerializer(rule, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        tenant_id = resolve_tenant_id(request.user)
        rule = ProductivityRule.objects.filter(tenant_id=tenant_id, pk=pk).first()
        if not rule:
            return Response(status=404)
        rule.delete()
        return Response(status=204)


class WFHProductivityMatrixView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        granularity = (request.query_params.get("granularity") or "daily").lower()
        if not tenant_id:
            return Response({"rows": [], "granularity": granularity})
        if granularity not in {"hourly", "daily"}:
            granularity = "daily"

        start_date = timezone.localdate() - timedelta(days=7 if granularity == "hourly" else 30)
        events = WorkSessionFocusEvent.objects.filter(
            tenant_id=tenant_id,
            occurred_at__date__gte=start_date,
        ).values("occurred_at", "focus_seconds", "is_productive")

        buckets: dict[str, dict] = {}
        for row in events:
            dt = row["occurred_at"]
            key = dt.strftime("%Y-%m-%d %H:00") if granularity == "hourly" else dt.strftime("%Y-%m-%d")
            bucket = buckets.setdefault(
                key,
                {"bucket": key, "productive_seconds": 0, "unproductive_seconds": 0, "total_seconds": 0},
            )
            sec = int(row["focus_seconds"] or 0)
            bucket["total_seconds"] += sec
            if row["is_productive"]:
                bucket["productive_seconds"] += sec
            else:
                bucket["unproductive_seconds"] += sec

        rows = []
        for key in sorted(buckets.keys(), reverse=True):
            b = buckets[key]
            total = b["total_seconds"] or 1
            b["productivity_ratio"] = round((b["productive_seconds"] / total) * 100, 2)
            rows.append(b)
        return Response({"granularity": granularity, "rows": rows})


class WFHUnproductiveTimelineView(APIView):
    permission_classes = [IsAuthenticated, CanViewEmployeeTracking]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response([])
        session_id = request.query_params.get("session_id")
        qs = WorkSessionFocusEvent.objects.filter(tenant_id=tenant_id, is_productive=False).select_related("screenshot")
        if session_id:
            qs = qs.filter(session_id=session_id)
        events = qs.order_by("-occurred_at")[:500]
        return Response(WorkSessionFocusEventSerializer(events, many=True).data)


class SessionScreenshotsView(APIView):
    permission_classes = [IsAuthenticated, CanViewEmployeeTracking]

    def get(self, request, session_id):
        session = WorkSession.objects.filter(pk=session_id).first()
        if not session:
            return Response(status=404)
        shots = ScreenshotCapture.objects.filter(session=session).order_by("captured_at")
        return Response(ScreenshotCaptureSerializer(shots, many=True).data)


class ScreenshotDetailView(APIView):
    permission_classes = [IsAuthenticated, CanViewEmployeeTracking]

    def get(self, request, pk):
        shot = ScreenshotCapture.objects.filter(pk=pk).select_related("session", "employee").first()
        if not shot:
            raise Http404
        perm = CanViewEmployeeTracking()
        if not perm.has_object_permission(request, self, shot):
            return Response({"detail": "Forbidden."}, status=403)
        audit_log(request, "screenshot.view", "ScreenshotCapture", shot.id)
        from core.storage import MissingSessionKeyError, ScreenshotDecryptError

        try:
            data = TrackerStorageService.read_screenshot_plaintext(
                shot.storage_key,
                shot.session,
                shot.checksum_sha256,
                shot.monitor_number,
            )
        except MissingSessionKeyError as exc:
            return Response({"detail": str(exc)}, status=422)
        except ScreenshotDecryptError as exc:
            import logging

            logging.getLogger(__name__).warning(
                "screenshot decrypt failed shot=%s session=%s: %s",
                shot.id,
                shot.session_id,
                exc,
            )
            return Response({"detail": str(exc)}, status=500)
        except Exception as exc:
            import logging

            logging.getLogger(__name__).exception(
                "screenshot load failed shot=%s", shot.id
            )
            return Response({"detail": "Unable to load screenshot."}, status=500)
        from io import BytesIO

        response = FileResponse(BytesIO(data), content_type="image/jpeg")
        response["Content-Disposition"] = 'inline; filename="screenshot.jpg"'
        response["Cache-Control"] = "private, max-age=300"
        return response


class SessionIdleSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = WorkSession.objects.filter(pk=session_id).first()
        if not session:
            return Response(status=404)
        return Response(
            {
                "session_id": str(session.id),
                "idle_duration": session.idle_duration,
                "active_duration": session.active_duration,
                "idle_logs": list(
                    session.idle_logs.values("idle_start_time", "idle_end_time", "idle_duration", "reason")
                ),
            }
        )


class TrackerSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from wfh.models import TrackerAppVersion

        tenant_id = resolve_tenant_id(request.user)
        policy = WFHPolicy.get_active(tenant_id) if tenant_id else None
        versions = TrackerAppVersion.objects.order_by("-created_at")[:5]
        return Response(
            {
                "policy": WFHPolicySerializer(policy).data if policy else None,
                "app_versions": TrackerAppVersionSerializer(versions, many=True).data,
            }
        )


class TrackerDevicesAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response([])
        devices = TrackerDevice.objects.filter(tenant_id=tenant_id).order_by("-last_seen_at")[:200]
        return Response(TrackerDeviceSerializer(devices, many=True).data)


class TrackerAuditLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = resolve_tenant_id(request.user)
        if not tenant_id:
            return Response({"results": [], "pagination": {"page": 1, "page_size": 50, "total": 0, "pages": 1}})

        qs = TrackerAuditLog.objects.filter(tenant_id=tenant_id).select_related("actor").order_by("-created_at")
        action = request.query_params.get("action")
        search = request.query_params.get("search")
        if action:
            qs = qs.filter(action__icontains=action)
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(action__icontains=search) | Q(entity_type__icontains=search))

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(200, max(1, int(request.query_params.get("page_size", 50))))
        except (TypeError, ValueError):
            page_size = 50

        total = qs.count()
        start = (page - 1) * page_size
        logs = qs[start : start + page_size]
        return Response({
            "results": TrackerAuditLogSerializer(logs, many=True).data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": max(1, (total + page_size - 1) // page_size),
            },
        })
