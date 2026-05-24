from celery import shared_task

from core.utilization import sample_utilization_and_maybe_cooldown


@shared_task
def sample_platform_utilization():
    return sample_utilization_and_maybe_cooldown()


@shared_task
def flush_clickhouse_log_buffer():
    from core.clickhouse_logs import flush_log_buffer
    flush_log_buffer()
    return "flushed"
