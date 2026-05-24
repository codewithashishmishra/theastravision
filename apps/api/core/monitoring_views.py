import csv
import io

import psutil
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.http import HttpResponse
from django.utils import timezone

from core.auth_views import get_user_role_names
from core.frontend_debug_log import append_frontend_debug_entry
from core.platform_config import frontend_debug_enabled
from core.utilization import build_status_payload, read_host_metrics
from core.metrics import get_summary_metrics, get_time_series, get_slow_endpoints
from core.log_sources.factory import get_log_source
from .models import AuthSession


class IsSuperAdminUser:
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return "Super Admin" in get_user_role_names(request.user)


def _is_it_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return "IT Admin" in get_user_role_names(user)


class PlatformStatusView(APIView):
    """Cooldown and utilization snapshot for all authenticated clients."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(build_status_payload())


class FrontendDebugLogView(APIView):
    """Ingest frontend HTTP debug entries when FRONTEND_DEBUG is enabled."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not frontend_debug_enabled():
            return Response(status=204)

        data = request.data
        if not isinstance(data, dict):
            return Response({"detail": "Invalid payload."}, status=400)

        direction = data.get("direction")
        if direction not in ("request", "response"):
            return Response({"detail": "direction must be 'request' or 'response'."}, status=400)

        append_frontend_debug_entry(data)
        return Response(status=204)


class PlatformMonitoringView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsSuperAdminUser().has_permission(request, self):
            return Response({"detail": "Super Admin access required."}, status=403)

        metrics = read_host_metrics()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        system_stats = {
            "cpu_usage_percent": metrics["cpu_usage_percent"],
            "ram_total_gb": round(memory.total / (1024**3), 2),
            "ram_used_gb": round(memory.used / (1024**3), 2),
            "ram_usage_percent": metrics["ram_usage_percent"],
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_usage_percent": disk.percent,
        }

        db_size_mb = 0
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_database_size(current_database()) / 1024 / 1024;"
                )
                row = cursor.fetchone()
                if row:
                    db_size_mb = row[0]
        except Exception:
            pass

        today = timezone.now().date()
        sessions_today = AuthSession.objects.filter(created_at__date=today)
        total_visits_today = sessions_today.count()
        methods_breakdown = {
            "password": 0,
            "totp": 0,
            "passkey": 0,
            "face_scan": 0,
        }
        for method in methods_breakdown.keys():
            methods_breakdown[method] = sessions_today.filter(
                login_method=method
            ).count()

        analytics = {
            "daily_visits_today": total_visits_today,
            "methods": methods_breakdown,
        }

        api_metrics = get_summary_metrics(minutes=60)
        status = build_status_payload()
        return Response(
            {
                "system": system_stats,
                "database": {"size_mb": db_size_mb},
                "analytics": analytics,
                "cooldown": status,
                "api_metrics": {
                    "error_rate_percent": api_metrics["error_rate_percent"],
                    "p50_latency_ms": api_metrics["p50_latency_ms"],
                    "p95_latency_ms": api_metrics["p95_latency_ms"],
                    "total_requests_1h": api_metrics["total_requests"],
                    "timeseries": api_metrics["timeseries"][-20:],
                },
            }
        )


class PlatformMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsSuperAdminUser().has_permission(request, self):
            return Response({"detail": "Super Admin access required."}, status=403)

        range_key = request.query_params.get("range", "1h")
        summary = get_summary_metrics(minutes={"1h": 60, "24h": 1440, "7d": 10080}.get(range_key, 60))
        return Response(
            {
                "range": range_key,
                "summary": summary,
                "timeseries": get_time_series(range_key),
                "slow_endpoints": get_slow_endpoints(),
            }
        )


class PlatformServicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsSuperAdminUser().has_permission(request, self) and not _is_it_admin(request.user):
            return Response({"detail": "Super Admin or IT Admin access required."}, status=403)
        source = get_log_source()
        return Response({"services": source.service_status()})


class PlatformSystemLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsSuperAdminUser().has_permission(request, self) and not _is_it_admin(request.user):
            return Response({"detail": "Super Admin or IT Admin access required."}, status=403)

        service = request.query_params.get("service")
        since = request.query_params.get("since")
        level = request.query_params.get("level")
        search = request.query_params.get("search")
        tenant_id = request.query_params.get("tenant_id")
        try:
            limit = min(500, max(1, int(request.query_params.get("limit", 200))))
        except (TypeError, ValueError):
            limit = 200

        if tenant_id:
            from core.audit_clickhouse import _ch_filters_from_request, fetch_logs_from_postgres
            from core.clickhouse_logs import clickhouse_enabled, query_tenant_logs

            if clickhouse_enabled():
                filters = _ch_filters_from_request(request, log_type="audit")
                filters.pop("log_type", None)
                filters["tenant_id"] = tenant_id
                entries = query_tenant_logs(filters, limit=limit)
                return Response({"results": entries, "count": len(entries), "source": "clickhouse"})

            rows = fetch_logs_from_postgres(request, tenant_id=tenant_id, limit=limit)
            return Response({"results": rows, "count": len(rows), "source": "postgres"})

        source = get_log_source()
        entries = source.tail(service=service, since=since, limit=limit, level=level, search=search)
        return Response({"results": [e.to_dict() for e in entries], "count": len(entries), "source": "stream"})


class PlatformSystemLogsExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsSuperAdminUser().has_permission(request, self) and not _is_it_admin(request.user):
            return Response({"detail": "Super Admin or IT Admin access required."}, status=403)

        fmt = request.query_params.get("format", "csv")
        service = request.query_params.get("service")
        since = request.query_params.get("since")
        level = request.query_params.get("level")
        search = request.query_params.get("search")

        source = get_log_source()
        entries = source.tail(service=service, since=since, limit=500, level=level, search=search)
        rows = [e.to_dict() for e in entries]

        if fmt == "json":
            return Response(rows)

        buffer = io.StringIO()
        if rows:
            writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="system-logs.csv"'
        return response
