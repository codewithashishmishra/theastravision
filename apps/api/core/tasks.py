from celery import shared_task

from core.utilization import sample_utilization_and_maybe_cooldown


@shared_task
def sample_platform_utilization():
    return sample_utilization_and_maybe_cooldown()
