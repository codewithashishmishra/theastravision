import time

from django.conf import settings

from core.metrics import record_request
from core.clickhouse_logs import enqueue_log_row
from core.tenant_utils import resolve_tenant_id


class RequestMetricsMiddleware:
    SKIP_PREFIXES = ("/admin/", "/static/", "/media/", "/api/schema")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "METRICS_ENABLED", True):
            return self.get_response(request)

        path = request.path
        if any(path.startswith(prefix) for prefix in self.SKIP_PREFIXES):
            return self.get_response(request)

        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000

        record_request(
            path=path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        if getattr(settings, "CLICKHOUSE_ENABLED", False) and response.status_code >= 400:
            tenant_id = None
            tenant_name = None
            user = getattr(request, "user", None)
            user_id = None
            user_email = None
            if user and user.is_authenticated:
                user_id = str(user.id)
                user_email = user.email
                tid = resolve_tenant_id(user)
                if tid:
                    tenant_id = str(tid)
                    if getattr(user, "tenant", None):
                        tenant_name = user.tenant.name
            enqueue_log_row(
                log_type="request",
                tenant_id=tenant_id,
                tenant_name=tenant_name,
                user_id=user_id,
                user_email=user_email,
                module="api",
                action=f"{request.method} {path}",
                level="ERROR" if response.status_code >= 500 else "WARN",
                service="api",
                message=f"{response.status_code} {request.method} {path} ({round(duration_ms, 2)}ms)",
                ip_address=request.META.get("REMOTE_ADDR"),
                metadata={"status_code": response.status_code, "duration_ms": round(duration_ms, 2)},
            )

        return response
