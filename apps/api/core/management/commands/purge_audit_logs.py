"""Purge SystemAuditLog and AuthSession rows older than AUDIT_LOG_RETENTION_DAYS."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import AuthSession, SystemAuditLog


class Command(BaseCommand):
    help = 'Delete audit logs and login sessions older than AUDIT_LOG_RETENTION_DAYS'

    def handle(self, *args, **options):
        days = settings.AUDIT_LOG_RETENTION_DAYS
        if days <= 0:
            self.stdout.write('AUDIT_LOG_RETENTION_DAYS is 0 — retention purge skipped.')
            return

        cutoff = timezone.now() - timedelta(days=days)
        audit_deleted, _ = SystemAuditLog.objects.filter(created_at__lt=cutoff).delete()
        session_deleted, _ = AuthSession.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f'Purged {audit_deleted} audit log row(s) and {session_deleted} login session row(s) '
                f'older than {days} days.'
            )
        )
