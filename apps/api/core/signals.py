from django.db.models.signals import post_save
from django.dispatch import receiver

from core.clickhouse_logs import enqueue_log_row, row_from_auth_session, row_from_system_audit_log
from core.models import AuthSession, SystemAuditLog


@receiver(post_save, sender=SystemAuditLog)
def mirror_audit_log_to_clickhouse(sender, instance, created, **kwargs):
    if not created:
        return
    enqueue_log_row(**row_from_system_audit_log(instance))


@receiver(post_save, sender=AuthSession)
def mirror_login_session_to_clickhouse(sender, instance, created, **kwargs):
    if not created:
        return
    enqueue_log_row(**row_from_auth_session(instance))
