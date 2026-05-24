"""Office hours window checks for field location pings."""

from datetime import datetime

import zoneinfo
from django.utils import timezone

from attendance.models import AttendanceSettings


def _default_work_days():
    return [1, 2, 3, 4, 5]


def is_within_office_hours(tenant_id) -> bool:
    settings = AttendanceSettings.objects.filter(tenant_id=tenant_id).first()
    if not settings:
        return True

    work_days = settings.work_days if settings.work_days else _default_work_days()
    tz_name = settings.office_hours_timezone or 'UTC'
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = timezone.get_current_timezone()

    now_local = timezone.now().astimezone(tz)
    if now_local.isoweekday() not in work_days:
        return False

    current_time = now_local.time()
    return settings.work_start_time <= current_time <= settings.work_end_time
