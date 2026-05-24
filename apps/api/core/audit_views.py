import csv
import io

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth_views import get_user_role_names
from core.models import AuthSession, SystemAuditLog
from core.audit import system_audit_log

from core.audit_serializers import AuthSessionSerializer, SystemAuditLogSerializer
from core.tenant_utils import resolve_tenant_id

AUDIT_ADMIN_MODULES = ["iam", "auth", "config", "employees", "payroll", "audit"]


def _is_super_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return "Super Admin" in get_user_role_names(user)


def _is_auditor(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return "Auditor" in get_user_role_names(user)


def _parse_date(value):
    if not value:
        return None
    try:
        from django.utils.dateparse import parse_datetime, parse_date

        dt = parse_datetime(value)
        if dt:
            return dt
        d = parse_date(value)
        if d:
            from datetime import datetime, time

            return timezone.make_aware(datetime.combine(d, time.min))
    except (ValueError, TypeError):
        pass
    return None


def _paginate_queryset(qs, request, default_page_size=50, max_page_size=200):
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max_page_size, max(1, int(request.query_params.get("page_size", default_page_size))))
    except (TypeError, ValueError):
        page_size = default_page_size
    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    return qs[start:end], {"page": page, "page_size": page_size, "total": total, "pages": max(1, (total + page_size - 1) // page_size)}


def _filter_audit_logs(qs, request):
    module = request.query_params.get("module")
    action = request.query_params.get("action")
    search = request.query_params.get("search")
    tenant_id = request.query_params.get("tenant_id")
    user_id = request.query_params.get("user_id")
    date_from = _parse_date(request.query_params.get("date_from"))
    date_to = _parse_date(request.query_params.get("date_to"))

    if module:
        qs = qs.filter(module=module)
    if action:
        qs = qs.filter(action__icontains=action)
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if user_id:
        qs = qs.filter(user_id=user_id)
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
    if search:
        qs = qs.filter(
            Q(action__icontains=search)
            | Q(module__icontains=search)
            | Q(user__email__icontains=search)
            | Q(tenant__name__icontains=search)
            | Q(metadata__icontains=search)
        )
    return qs


def _filter_login_sessions(qs, request):
    search = request.query_params.get("search")
    login_method = request.query_params.get("login_method")
    client_type = request.query_params.get("client_type")
    revoked = request.query_params.get("revoked")
    tenant_id = request.query_params.get("tenant_id")
    date_from = _parse_date(request.query_params.get("date_from"))
    date_to = _parse_date(request.query_params.get("date_to"))

    if tenant_id:
        qs = qs.filter(user__tenant_id=tenant_id)

    if login_method:
        qs = qs.filter(login_method=login_method)
    if client_type:
        qs = qs.filter(client_type=client_type)
    if revoked is not None:
        qs = qs.filter(is_revoked=revoked.lower() in ("1", "true", "yes"))
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
    if search:
        qs = qs.filter(
            Q(user__email__icontains=search)
            | Q(ip_address__icontains=search)
            | Q(location_city__icontains=search)
            | Q(location_country__icontains=search)
        )
    return qs


class PlatformAuditLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_super_admin(request.user):
            return Response({"detail": "Super Admin access required."}, status=403)

        from core.audit_clickhouse import fetch_logs_from_clickhouse

        ch = fetch_logs_from_clickhouse(request, log_type="audit")
        if ch:
            rows, pagination = ch
            return Response({"results": rows, "pagination": pagination, "source": "clickhouse"})

        qs = SystemAuditLog.objects.select_related("user", "tenant").order_by("-created_at")
        qs = _filter_audit_logs(qs, request)
        page_qs, pagination = _paginate_queryset(qs, request)
        return Response({
            "results": SystemAuditLogSerializer(page_qs, many=True).data,
            "pagination": pagination,
            "source": "postgres",
        })


class AdminActionsAuditView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_auditor(request.user) and not _is_super_admin(request.user):
            return Response({"detail": "Auditor access required."}, status=403)

        from core.audit_clickhouse import effective_tenant_id, fetch_logs_from_clickhouse

        tenant_id = effective_tenant_id(request, request.user)
        if not tenant_id and not _is_super_admin(request.user):
            return Response({"detail": "Tenant required."}, status=403)

        if not request.query_params.get("tenant_id") and tenant_id:
            ch = fetch_logs_from_clickhouse(
                request, log_type="audit", module_in=AUDIT_ADMIN_MODULES, tenant_id=tenant_id
            )
        else:
            ch = fetch_logs_from_clickhouse(request, log_type="audit", module_in=AUDIT_ADMIN_MODULES)
        if ch:
            rows, pagination = ch
            return Response({"results": rows, "pagination": pagination, "source": "clickhouse"})

        qs = SystemAuditLog.objects.select_related("user", "tenant").order_by("-created_at")
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        qs = qs.filter(module__in=AUDIT_ADMIN_MODULES)
        qs = _filter_audit_logs(qs, request)
        page_qs, pagination = _paginate_queryset(qs, request)
        return Response({
            "results": SystemAuditLogSerializer(page_qs, many=True).data,
            "pagination": pagination,
            "source": "postgres",
        })


class LoginSessionsAuditView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_auditor(request.user) and not _is_super_admin(request.user):
            return Response({"detail": "Auditor access required."}, status=403)

        from core.audit_clickhouse import ch_row_to_login_session, effective_tenant_id, fetch_logs_from_clickhouse

        tenant_id = effective_tenant_id(request, request.user)
        if not tenant_id and not _is_super_admin(request.user):
            return Response({"detail": "Tenant required."}, status=403)

        ch = fetch_logs_from_clickhouse(
            request,
            log_type="login",
            tenant_id=tenant_id if not request.query_params.get("tenant_id") else None,
        )
        if ch:
            rows, pagination = ch
            return Response({
                "results": [ch_row_to_login_session(r) for r in rows],
                "pagination": pagination,
                "source": "clickhouse",
            })

        qs = AuthSession.objects.select_related("user", "user__tenant").order_by("-created_at")
        if tenant_id:
            qs = qs.filter(user__tenant_id=tenant_id)
        tenant_filter = request.query_params.get("tenant_id")
        if tenant_filter and _is_super_admin(request.user):
            qs = qs.filter(user__tenant_id=tenant_filter)
        qs = _filter_login_sessions(qs, request)
        page_qs, pagination = _paginate_queryset(qs, request)
        return Response({
            "results": AuthSessionSerializer(page_qs, many=True).data,
            "pagination": pagination,
            "source": "postgres",
        })


class AuditExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        export_type = request.query_params.get("type", "platform")
        fmt = request.query_params.get("format", "csv")

        if export_type == "platform":
            if not _is_super_admin(request.user):
                return Response({"detail": "Super Admin access required."}, status=403)
            qs = SystemAuditLog.objects.select_related("user", "tenant").order_by("-created_at")
            qs = _filter_audit_logs(qs, request)[:5000]
            rows = SystemAuditLogSerializer(qs, many=True).data
            filename = "platform-audit-logs"
        elif export_type == "admin":
            if not _is_auditor(request.user) and not _is_super_admin(request.user):
                return Response({"detail": "Auditor access required."}, status=403)
            tenant_id = resolve_tenant_id(request.user)
            qs = SystemAuditLog.objects.select_related("user", "tenant").order_by("-created_at")
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            qs = qs.filter(module__in=AUDIT_ADMIN_MODULES)
            qs = _filter_audit_logs(qs, request)[:5000]
            rows = SystemAuditLogSerializer(qs, many=True).data
            filename = "admin-audit-logs"
        elif export_type == "login":
            if not _is_auditor(request.user) and not _is_super_admin(request.user):
                return Response({"detail": "Auditor access required."}, status=403)
            tenant_id = resolve_tenant_id(request.user)
            qs = AuthSession.objects.select_related("user").order_by("-created_at")
            if tenant_id:
                qs = qs.filter(user__tenant_id=tenant_id)
            qs = _filter_login_sessions(qs, request)[:5000]
            rows = AuthSessionSerializer(qs, many=True).data
            filename = "login-sessions"
        else:
            return Response({"detail": "Invalid type."}, status=400)

        system_audit_log(
            request,
            action="audit.export",
            module="audit",
            metadata={"export_type": export_type, "format": fmt, "row_count": len(rows)},
        )

        if fmt == "json":
            return Response(rows)

        if not rows:
            rows = [{}]

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in rows[0].keys()})

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        return response
