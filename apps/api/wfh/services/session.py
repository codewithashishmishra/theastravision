from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from wfh.models import WFHRequest, WorkSession


def get_approved_wfh_for_today(employee):
    today = timezone.localdate()
    qs = WFHRequest.objects.filter(
        employee=employee,
        start_date__lte=today,
        end_date__gte=today,
    ).exclude(status__in=[WFHRequest.STATUS_REJECTED, WFHRequest.STATUS_CANCELLED])
    for req in qs:
        if req.is_wfh_approved:
            return req
    return None


def finalize_session(session: WorkSession):
    now = timezone.now()
    if not session.end_time:
        session.end_time = now
    delta = session.end_time - session.start_time
    session.total_duration = int(delta.total_seconds())
    reported = (session.active_duration or 0) + (session.idle_duration or 0) + (session.paused_duration or 0)
    if reported == 0 and session.total_duration > 0:
        # Report missing or empty — use wall-clock time as active
        session.active_duration = session.total_duration
    elif reported > session.total_duration:
        session.active_duration = max(
            0,
            session.total_duration - session.idle_duration - session.paused_duration,
        )
    session.save()
    return session


def get_active_session(employee):
    return WorkSession.objects.filter(
        employee=employee,
        status__in=[WorkSession.STATUS_ACTIVE, WorkSession.STATUS_PAUSED],
    ).first()
