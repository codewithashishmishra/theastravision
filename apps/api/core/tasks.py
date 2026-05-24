from celery import shared_task

from core.utilization import sample_utilization_and_maybe_cooldown


@shared_task
def sample_platform_utilization():
    return sample_utilization_and_maybe_cooldown()


@shared_task
def flush_clickhouse_log_buffer():
    from core.clickhouse_logs import clickhouse_enabled, flush_log_buffer

    if not clickhouse_enabled():
        return "skipped"
    flush_log_buffer()
    return "flushed"


@shared_task
def purge_audit_logs():
    from django.core.management import call_command
    call_command('purge_audit_logs')
    return "purged"
