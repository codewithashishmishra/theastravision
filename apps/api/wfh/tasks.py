from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from core.storage import TrackerStorageService
from notifications.models import Notification
from wfh.models import ActivitySummary, ScreenshotCapture, WFHPolicy, WFHRequest, WorkSession


@shared_task
def close_stale_sessions():
    now = timezone.now()
    active = WorkSession.objects.filter(status__in=[WorkSession.STATUS_ACTIVE, WorkSession.STATUS_PAUSED])
    for session in active:
        policy = WFHPolicy.get_active(session.tenant_id)
        miss_seconds = policy.heartbeat_miss_seconds if policy else 180
        last_hb = session.heartbeats.order_by("-heartbeat_at").first()
        if last_hb and (now - last_hb.heartbeat_at).total_seconds() > miss_seconds:
            session.status = WorkSession.STATUS_INTERRUPTED
            session.end_time = now
            session.save(update_fields=["status", "end_time", "updated_at"])


@shared_task
def purge_expired_screenshots():
    now = timezone.now()
    for policy in WFHPolicy.objects.filter(is_active=True):
        cutoff = now - timedelta(days=policy.screenshot_retention_days)
        shots = ScreenshotCapture.objects.filter(tenant=policy.tenant, captured_at__lt=cutoff)
        for shot in shots[:500]:
            TrackerStorageService.delete_file(shot.storage_key)
            if shot.thumbnail_key:
                TrackerStorageService.delete_file(shot.thumbnail_key)
            shot.delete()


@shared_task
def build_daily_activity_summary():
    yesterday = timezone.localdate() - timedelta(days=1)
    for session in WorkSession.objects.filter(start_time__date=yesterday):
        total = session.total_duration or 0
        idle = session.idle_duration or 0
        active = max(0, total - idle)
        score = (active / total * 100) if total else 0
        ActivitySummary.objects.update_or_create(
            tenant=session.tenant,
            employee=session.employee,
            session=session,
            summary_date=yesterday,
            defaults={
                "active_seconds": active,
                "idle_seconds": idle,
                "screenshot_count": session.screenshot_count,
                "productivity_score": round(score, 2),
            },
        )


@shared_task
def notify_tracker_not_started():
    today = timezone.localdate()
    approved = WFHRequest.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
    ).exclude(status__in=[WFHRequest.STATUS_REJECTED, WFHRequest.STATUS_CANCELLED])
    for req in approved:
        if not req.is_wfh_approved or not req.employee.user_id:
            continue
        has_session = WorkSession.objects.filter(
            employee=req.employee, start_time__date=today
        ).exists()
        if not has_session:
            Notification.objects.create(
                tenant=req.tenant,
                user=req.employee.user,
                title="Start WFH Tracker",
                message="You have approved WFH today. Please start the desktop tracker when you begin work.",
                channel="In-App",
            )
