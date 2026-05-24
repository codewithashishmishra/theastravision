from django.utils import timezone as dj_timezone

from core.timezone_utils import activate_viewing_timezone, is_audit_path


class TimezoneMiddleware:
    """Activate regional timezone for session-authenticated requests; always deactivate after."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_activated = False
        if not is_audit_path(request.path):
            user = getattr(request, "user", None)
            if user and user.is_authenticated and not getattr(request, "_timezone_activated", False):
                activate_viewing_timezone(request, user=user)
                session_activated = True

        try:
            return self.get_response(request)
        finally:
            if getattr(request, "_timezone_activated", False) or session_activated:
                dj_timezone.deactivate()
