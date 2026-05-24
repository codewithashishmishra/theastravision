import psutil
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.utils import timezone
from datetime import timedelta

from core.auth_views import get_user_role_names
from core.utilization import build_status_payload, read_host_metrics
from .models import AuthSession


class IsSuperAdminUser:
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return "Super Admin" in get_user_role_names(request.user)


class PlatformStatusView(APIView):
    """Cooldown and utilization snapshot for all authenticated clients."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(build_status_payload())


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

        status = build_status_payload()
        return Response(
            {
                "system": system_stats,
                "database": {"size_mb": db_size_mb},
                "analytics": analytics,
                "cooldown": status,
            }
        )
