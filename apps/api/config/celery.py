import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("aastraahr")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

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
        "schedule": 30.0,
    },
    "cleanup-expired-ai-interviews": {
        "task": "recruitment.tasks.cleanup_expired_sessions",
        "schedule": crontab(minute="*/15"),
    },
}
