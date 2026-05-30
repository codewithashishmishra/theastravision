from django.utils import timezone

from wfh.models import ActivitySummary, WorkSession, WorkSessionEvent, WorkSessionFocusEvent
from wfh.services.productivity import classify_focus


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
    focus_segments = payload.get("focus_segments") or []

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

    focus_rows = []
    productive_seconds = 0
    unproductive_seconds = 0
    for seg in focus_segments:
        app_name = (seg.get("application_name") or "").strip()
        tab_title = (seg.get("active_tab_title") or "").strip()
        window_title = (seg.get("window_title") or "").strip()
        seconds = int(seg.get("focus_seconds") or 0)
        is_productive, matched_rule = classify_focus(
            tenant_id=session.tenant_id,
            app_name=app_name,
            tab_title=tab_title,
        )
        if is_productive:
            productive_seconds += seconds
        else:
            unproductive_seconds += seconds
        focus_rows.append(
            WorkSessionFocusEvent(
                tenant=session.tenant,
                session=session,
                employee=employee,
                occurred_at=seg.get("timestamp") or timezone.now(),
                application_name=app_name[:255],
                active_tab_title=tab_title[:512],
                window_title=window_title[:512],
                focus_seconds=seconds,
                is_productive=is_productive,
                matched_rule=matched_rule,
            )
        )
    if focus_rows:
        WorkSessionFocusEvent.objects.bulk_create(focus_rows)

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
    tracked_total = productive_seconds + unproductive_seconds
    if tracked_total == 0:
        productive_seconds = active
        tracked_total = max(active, 1)
        unproductive_seconds = max(tracked_total - productive_seconds, 0)
    score = (productive_seconds / tracked_total * 100) if tracked_total else 0
    ActivitySummary.objects.update_or_create(
        tenant=session.tenant,
        employee=employee,
        session=session,
        summary_date=today,
        defaults={
            "active_seconds": active,
            "idle_seconds": idle,
            "screenshot_count": session.screenshot_count,
            "productive_seconds": productive_seconds,
            "unproductive_seconds": unproductive_seconds,
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
