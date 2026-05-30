import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("aastraahr")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

_debug = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
_utilization_interval = 120.0 if _debug else 30.0

app.conf.beat_schedule = {
    "close-stale-wfh-sessions": {
        "task": "wfh.tasks.close_stale_sessions",
        "schedule": crontab(minute="*/5"),
    },
    "purge-expired-screenshots": {
        "task": "wfh.tasks.purge_expired_screenshots",
        "schedule": crontab(hour=2, minute=0),
    },
    "build-daily-activity-summary": {
        "task": "wfh.tasks.build_daily_activity_summary",
        "schedule": crontab(hour=1, minute=0),
    },
    "notify-tracker-not-started": {
        "task": "wfh.tasks.notify_tracker_not_started",
        "schedule": crontab(hour=10, minute=0),
    },
    "sample-platform-utilization": {
        "task": "core.tasks.sample_platform_utilization",
        "schedule": _utilization_interval,
    },
    "flush-clickhouse-log-buffer": {
        "task": "core.tasks.flush_clickhouse_log_buffer",
        "schedule": 30.0,
    },
    "purge-audit-logs": {
        "task": "core.tasks.purge_audit_logs",
        "schedule": crontab(hour=3, minute=30),
    },
    "cleanup-expired-ai-interviews": {
        "task": "recruitment.tasks.cleanup_expired_sessions",
        "schedule": crontab(minute="*/15"),
    },
    "purge-expired-interview-media": {
        "task": "recruitment.tasks.purge_expired_interview_media",
        "schedule": crontab(hour=2, minute=30),
    },
    "process-cold-campaign-followups": {
        "task": "cold_campaign.tasks.process_cold_campaign_followups",
        "schedule": crontab(minute="*/15"),
    },
    "poll-cold-campaign-replies": {
        "task": "cold_campaign.tasks.poll_cold_campaign_replies",
        "schedule": crontab(minute="*/5"),
    },
}
