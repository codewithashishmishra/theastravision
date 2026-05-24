"""PostgreSQL-backed session store table (named REDIS when REDIS_ALLOW=False)."""

from django.db import models


class Redis(models.Model):
    """E2EE session blobs at rest — table name REDIS per deployment spec."""

    session_id = models.CharField(max_length=64, primary_key=True)
    payload = models.BinaryField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "REDIS"
        indexes = [
            models.Index(fields=["expires_at"], name="redis_expires_at_idx"),
        ]
