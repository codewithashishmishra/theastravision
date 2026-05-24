import json

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from core.platform_config import super_admin_bypass_enabled, utilization_enabled
from core.utilization import build_cooldown_payload, is_cooldown_active

COOLDOWN_EXEMPT_PREFIXES = (
    "/api/v1/auth/login/",
    "/api/v1/auth/token/",
    "/api/v1/tracker/auth/",
    "/api/v1/platform/status/",
    "/admin/",
    "/api/schema/",
    "/static/",
    "/media/",
)

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _path_exempt(path: str) -> bool:
    for prefix in COOLDOWN_EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return True
    if path == "/api/v1/auth/token/refresh/":
        return True
    return False


def _super_admin_bypass(request) -> bool:
    if not super_admin_bypass_enabled():
        return False
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    from core.auth_views import get_user_role_names

    return "Super Admin" in get_user_role_names(user)


class PlatformCooldownMiddleware(MiddlewareMixin):
    """Return 503 for mutating API calls while platform cooldown is active."""

    def process_request(self, request):
        if request.method not in MUTATING_METHODS:
            return None
        if _path_exempt(request.path):
            return None
        if not request.path.startswith("/api/"):
            return None
        if not utilization_enabled():
            return None
        if _super_admin_bypass(request):
            return None
        if not is_cooldown_active():
            return None

        payload = build_cooldown_payload()
        response = JsonResponse(payload, status=503)
        response["Retry-After"] = str(payload["retry_after_seconds"])
        return response
