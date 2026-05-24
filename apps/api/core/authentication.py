from django.utils import timezone as dj_timezone
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.timezone_utils import activate_viewing_timezone, is_audit_path


class TimezoneJWTAuthentication(JWTAuthentication):
    """JWT auth that activates the viewer's regional timezone for DRF serialization."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result and not is_audit_path(request.path):
            user, _token = result
            activate_viewing_timezone(request, user=user)
        return result
