from django.core.management.base import BaseCommand

from core.clickhouse_logs import enqueue_log_row, flush_log_buffer, row_from_auth_session, row_from_system_audit_log
from core.models import AuthSession, SystemAuditLog


class Command(BaseCommand):
    help = "Backfill PostgreSQL audit/login logs into ClickHouse (batched inserts)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50000, help="Max rows per table to backfill")

    def handle(self, *args, **options):
        limit = options["limit"]
        audit_count = 0
        login_count = 0

        for log in SystemAuditLog.objects.select_related("user", "tenant").order_by("created_at")[:limit]:
            enqueue_log_row(**row_from_system_audit_log(log))
            audit_count += 1

        for session in AuthSession.objects.select_related("user", "user__tenant").order_by("created_at")[:limit]:
            enqueue_log_row(**row_from_auth_session(session))
            login_count += 1

        flush_log_buffer()
        self.stdout.write(self.style.SUCCESS(f"Queued {audit_count} audit + {login_count} login rows to ClickHouse"))
