"""ClickHouse batched platform log storage (5000-row inserts)."""

from __future__ import annotations

import atexit
import json
import logging
import threading
import uuid
from datetime import datetime, timezone

from django.conf import settings

logger = logging.getLogger(__name__)

_buffer: list[dict] = []
_lock = threading.Lock()
_client = None
_schema_ready = False

COLUMNS = [
    "id",
    "log_type",
    "tenant_id",
    "tenant_name",
    "user_id",
    "user_email",
    "module",
    "action",
    "level",
    "service",
    "message",
    "ip_address",
    "metadata",
    "created_at",
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS platform_logs (
    id UUID,
    log_type LowCardinality(String),
    tenant_id UUID,
    tenant_name Nullable(String),
    user_id Nullable(UUID),
    user_email Nullable(String),
    module String,
    action String,
    level LowCardinality(String),
    service LowCardinality(String),
    message String,
    ip_address Nullable(String),
    metadata String,
    created_at DateTime64(3, 'UTC')
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (log_type, tenant_id, created_at)
"""


def clickhouse_enabled() -> bool:
    return getattr(settings, "CLICKHOUSE_ENABLED", False)


def _get_client():
    global _client, _schema_ready
    if _client is not None:
        return _client
    try:
        import clickhouse_connect
    except ImportError:
        logger.warning("clickhouse-connect not installed; log batching disabled")
        return None

    host = getattr(settings, "CLICKHOUSE_HOST", "localhost")
    port = int(getattr(settings, "CLICKHOUSE_PORT", 8123))
    user = getattr(settings, "CLICKHOUSE_USER", "default")
    password = getattr(settings, "CLICKHOUSE_PASSWORD", "")
    database = getattr(settings, "CLICKHOUSE_DATABASE", "default")

    try:
        _client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password,
            database=database,
        )
        if not _schema_ready:
            _client.command(CREATE_TABLE_SQL)
            _schema_ready = True
        return _client
    except Exception as exc:
        logger.warning("ClickHouse connection failed: %s", exc)
        return None


def _row_tuple(row: dict):
    created = row.get("created_at")
    if isinstance(created, str):
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
    elif isinstance(created, datetime):
        created_dt = created
    else:
        created_dt = datetime.now(timezone.utc)

    if created_dt.tzinfo is None:
        created_dt = created_dt.replace(tzinfo=timezone.utc)

    tenant_id = row.get("tenant_id")
    user_id = row.get("user_id")

    return [
        uuid.UUID(str(row.get("id") or uuid.uuid4())),
        row.get("log_type") or "audit",
        uuid.UUID(str(tenant_id)) if tenant_id else uuid.UUID(int=0),
        row.get("tenant_name") or None,
        uuid.UUID(str(user_id)) if user_id else None,
        row.get("user_email") or None,
        row.get("module") or "",
        row.get("action") or "",
        row.get("level") or "",
        row.get("service") or "",
        row.get("message") or "",
        row.get("ip_address") or None,
        json.dumps(row.get("metadata") or {}, default=str),
        created_dt,
    ]


def _flush_rows(rows: list[dict]):
    if not rows:
        return
    client = _get_client()
    if client is None:
        return
    try:
        data = [_row_tuple(r) for r in rows]
        client.insert("platform_logs", data, column_names=COLUMNS)
    except Exception as exc:
        logger.exception("ClickHouse batch insert failed (%s rows): %s", len(rows), exc)


def flush_log_buffer():
    """Flush pending rows (partial batch). Called on interval and process exit."""
    with _lock:
        if not _buffer:
            return
        rows = list(_buffer)
        _buffer.clear()
    _flush_rows(rows)


def enqueue_log_row(**fields):
    """Add a log row to the in-memory buffer; flush when batch size reached."""
    if not clickhouse_enabled():
        return

    row = {
        "id": str(fields.get("id") or uuid.uuid4()),
        "log_type": fields.get("log_type", "audit"),
        "tenant_id": str(fields["tenant_id"]) if fields.get("tenant_id") else None,
        "tenant_name": fields.get("tenant_name"),
        "user_id": str(fields["user_id"]) if fields.get("user_id") else None,
        "user_email": fields.get("user_email"),
        "module": fields.get("module", ""),
        "action": fields.get("action", ""),
        "level": fields.get("level", ""),
        "service": fields.get("service", ""),
        "message": fields.get("message", ""),
        "ip_address": fields.get("ip_address"),
        "metadata": fields.get("metadata") or {},
        "created_at": fields.get("created_at") or datetime.now(timezone.utc).isoformat(),
    }

    batch_size = int(getattr(settings, "CLICKHOUSE_BATCH_SIZE", 5000))
    with _lock:
        _buffer.append(row)
        should_flush = len(_buffer) >= batch_size
        if should_flush:
            rows = list(_buffer)
            _buffer.clear()
        else:
            rows = None

    if rows:
        _flush_rows(rows)


def row_from_system_audit_log(instance):
    tenant = instance.tenant
    user = instance.user
    return {
        "id": str(instance.id),
        "log_type": "audit",
        "tenant_id": str(tenant.id) if tenant else None,
        "tenant_name": tenant.name if tenant else None,
        "user_id": str(user.id) if user else None,
        "user_email": user.email if user else None,
        "module": instance.module,
        "action": instance.action,
        "message": instance.action,
        "ip_address": instance.ip_address,
        "metadata": instance.metadata,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
    }


def row_from_auth_session(instance):
    user = instance.user
    tenant = getattr(user, "tenant", None)
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, f"auth-session-{instance.id}")),
        "log_type": "login",
        "tenant_id": str(tenant.id) if tenant else None,
        "tenant_name": tenant.name if tenant else None,
        "user_id": str(user.id) if user else None,
        "user_email": user.email if user else None,
        "module": "auth",
        "action": f"auth.session.{instance.login_method}",
        "message": f"Login via {instance.login_method} ({instance.client_type})",
        "ip_address": instance.ip_address,
        "metadata": {
            "session_id": instance.id,
            "client_type": instance.client_type,
            "login_method": instance.login_method,
            "location_city": instance.location_city,
            "location_country": instance.location_country,
            "is_revoked": instance.is_revoked,
        },
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
    }


def _build_where(filters: dict) -> tuple[str, dict]:
    clauses = ["1 = 1"]
    params: dict = {}

    log_type = filters.get("log_type")
    if log_type:
        clauses.append("log_type = {log_type:String}")
        params["log_type"] = log_type

    tenant_id = filters.get("tenant_id")
    if tenant_id:
        clauses.append("tenant_id = {tenant_id:UUID}")
        params["tenant_id"] = tenant_id

    tenant_name = filters.get("tenant_name")
    if tenant_name:
        clauses.append("positionCaseInsensitive(tenant_name, {tenant_name:String}) > 0")
        params["tenant_name"] = tenant_name

    module = filters.get("module")
    if module:
        clauses.append("positionCaseInsensitive(module, {module:String}) > 0")
        params["module"] = module

    action = filters.get("action")
    if action:
        clauses.append("positionCaseInsensitive(action, {action:String}) > 0")
        params["action"] = action

    if filters.get("module_in"):
        modules = filters["module_in"]
        clauses.append("module IN {modules:Array(String)}")
        params["modules"] = modules

    level = filters.get("level")
    if level:
        clauses.append("level = {level:String}")
        params["level"] = level

    service = filters.get("service")
    if service:
        clauses.append("service = {service:String}")
        params["service"] = service

    search = filters.get("search")
    if search:
        clauses.append(
            "(positionCaseInsensitive(message, {search:String}) > 0 "
            "OR positionCaseInsensitive(action, {search:String}) > 0 "
            "OR positionCaseInsensitive(user_email, {search:String}) > 0 "
            "OR positionCaseInsensitive(metadata, {search:String}) > 0)"
        )
        params["search"] = search

    date_from = filters.get("date_from")
    if date_from:
        clauses.append("created_at >= {date_from:DateTime64(3)}")
        params["date_from"] = date_from

    date_to = filters.get("date_to")
    if date_to:
        clauses.append("created_at <= {date_to:DateTime64(3)}")
        params["date_to"] = date_to

    return " AND ".join(clauses), params


def query_logs(filters: dict | None = None, *, page: int = 1, page_size: int = 50) -> tuple[list[dict], int]:
    """Query logs from ClickHouse with pagination. Returns (rows, total)."""
    if not clickhouse_enabled():
        return [], 0

    client = _get_client()
    if client is None:
        return [], 0

    filters = filters or {}
    where_sql, params = _build_where(filters)
    offset = (max(1, page) - 1) * page_size

    try:
        count_result = client.query(
            f"SELECT count() FROM platform_logs WHERE {where_sql}",
            parameters=params,
        )
        total = int(count_result.result_rows[0][0]) if count_result.result_rows else 0

        params_with_page = {**params, "limit": page_size, "offset": offset}
        result = client.query(
            f"""
            SELECT id, log_type, tenant_id, tenant_name, user_id, user_email,
                   module, action, level, service, message, ip_address, metadata, created_at
            FROM platform_logs
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT {{limit:UInt32}} OFFSET {{offset:UInt32}}
            """,
            parameters=params_with_page,
        )
    except Exception as exc:
        logger.exception("ClickHouse query failed: %s", exc)
        return [], 0

    rows = []
    for r in result.result_rows:
        metadata_raw = r[12]
        try:
            metadata = json.loads(metadata_raw) if metadata_raw else {}
        except json.JSONDecodeError:
            metadata = {"raw": metadata_raw}

        created = r[13]
        if isinstance(created, datetime):
            created_iso = created.astimezone(timezone.utc).isoformat()
        else:
            created_iso = str(created)

        rows.append(
            {
                "id": str(r[0]),
                "log_type": r[1],
                "tenant": str(r[2]) if r[2] else None,
                "tenant_id": str(r[2]) if r[2] else None,
                "tenant_name": r[3],
                "user": str(r[4]) if r[4] else None,
                "user_id": str(r[4]) if r[4] else None,
                "user_email": r[5],
                "module": r[6],
                "action": r[7],
                "level": r[8],
                "service": r[9],
                "message": r[10],
                "ip_address": r[11],
                "metadata": metadata,
                "created_at": created_iso,
            }
        )
    return rows, total


def query_tenant_logs(filters: dict | None = None, *, limit: int = 200) -> list[dict]:
    """All log types for a tenant (audit, login, request, system)."""
    f = dict(filters or {})
    rows, _ = query_logs(f, page=1, page_size=limit)
    entries = []
    for row in rows:
        entries.append(
            {
                "timestamp": row["created_at"],
                "level": row.get("level") or row.get("log_type", "INFO").upper(),
                "service": row.get("service") or row.get("module") or row.get("log_type") or "platform",
                "message": row.get("message") or row.get("action") or "",
                "raw": json.dumps(row, default=str),
                "metadata": {
                    **(row.get("metadata") or {}),
                    "tenant_id": row.get("tenant_id"),
                    "tenant_name": row.get("tenant_name"),
                    "log_type": row.get("log_type"),
                },
            }
        )
    return entries


def query_system_log_entries(filters: dict | None = None, *, limit: int = 200) -> list[dict]:
    """Shape ClickHouse rows as system log explorer entries."""
    f = dict(filters or {})
    if "log_type" not in f:
        f["log_type"] = "system"
    rows, _ = query_logs(f, page=1, page_size=limit)

    entries = []
    for row in rows:
        entries.append(
            {
                "timestamp": row["created_at"],
                "level": row.get("level") or "INFO",
                "service": row.get("service") or row.get("module") or "platform",
                "message": row.get("message") or row.get("action") or "",
                "raw": json.dumps(row, default=str),
                "metadata": {
                    **(row.get("metadata") or {}),
                    "tenant_id": row.get("tenant_id"),
                    "tenant_name": row.get("tenant_name"),
                },
            }
        )
    return entries


atexit.register(flush_log_buffer)
