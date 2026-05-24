from django.utils import timezone

from wfh.models import ActivitySummary, WorkSession, WorkSessionEvent


def _map_event_type(raw: str) -> str:
    allowed = {c[0] for c in WorkSessionEvent.EVENT_CHOICES}
    if raw in allowed:
        return raw
    mapping = {
        "auto_idle": WorkSessionEvent.EVENT_AUTO_PAUSE,
        "manual": WorkSessionEvent.EVENT_PAUSE,
    }
    return mapping.get(raw, WorkSessionEvent.EVENT_PAUSE)


def persist_session_report(session: WorkSession, employee, payload: dict):
    """Bulk-create events and update session totals + activity summary."""
    events = payload.get("events") or []
    totals = payload.get("totals") or {}
    spoof_flags = payload.get("spoof_flags") or []

    to_create = []
    for ev in events:
        et = _map_event_type(ev.get("event_type", ""))
        to_create.append(
            WorkSessionEvent(
                tenant=session.tenant,
                session=session,
                employee=employee,
                event_type=et,
                occurred_at=ev.get("occurred_at") or timezone.now(),
                detail=(ev.get("detail") or "")[:512],
                metadata=ev.get("metadata") or {},
            )
        )
    if to_create:
        WorkSessionEvent.objects.bulk_create(to_create)

    active = int(totals.get("active", totals.get("active_sec", 0)) or 0)
    idle = int(totals.get("idle", totals.get("idle_sec", 0)) or 0)
    paused = int(totals.get("paused", totals.get("paused_sec", 0)) or 0)

    session.active_duration = active
    session.idle_duration = idle
    session.paused_duration = paused
    if payload.get("task_title"):
        session.task_title = str(payload["task_title"])[:255]
    if payload.get("task_description"):
        session.task_description = payload["task_description"]
    session.save(
        update_fields=[
            "active_duration",
            "idle_duration",
            "paused_duration",
            "task_title",
            "task_description",
            "updated_at",
        ]
    )

    today = timezone.localdate()
    total = session.total_duration or (active + idle + paused)
    score = (active / total * 100) if total else 0
    ActivitySummary.objects.update_or_create(
        tenant=session.tenant,
        employee=employee,
        session=session,
        summary_date=today,
        defaults={
            "active_seconds": active,
            "idle_seconds": idle,
            "screenshot_count": session.screenshot_count,
            "productivity_score": round(score, 2),
        },
    )

    WorkSessionEvent.objects.create(
        tenant=session.tenant,
        session=session,
        employee=employee,
        event_type=WorkSessionEvent.EVENT_SESSION_STOP,
        occurred_at=timezone.now(),
        detail="Session report submitted",
        metadata={"spoof_flags": spoof_flags, "paused_seconds": paused},
    )
