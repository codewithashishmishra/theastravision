"""DRF fields for regional vs UTC datetime API output."""

from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.utils import timezone as dj_timezone
from rest_framework import serializers

from core.timezone_utils import is_valid_timezone


class RegionalDateTimeField(serializers.DateTimeField):
    """Serialize datetimes in the viewer's regional timezone.

    Uses ``request.viewing_timezone`` when set by auth/middleware, otherwise the
    thread-local timezone from ``django.utils.timezone.activate``.
    """

    def _viewing_zone(self):
        request = self.context.get("request") if self.context else None
        tz_name = getattr(request, "viewing_timezone", None) if request else None
        if tz_name and is_valid_timezone(tz_name):
            return ZoneInfo(tz_name)
        return dj_timezone.get_current_timezone()

    def default_timezone(self):
        return self._viewing_zone()


class UtcDateTimeField(serializers.DateTimeField):
    """Always serialize datetimes in UTC (audit / compliance trails)."""

    def default_timezone(self):
        return dt_timezone.utc
