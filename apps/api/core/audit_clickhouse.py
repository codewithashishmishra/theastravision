"""Helpers for audit API — ClickHouse queries with PostgreSQL fallback."""

from core.clickhouse_logs import clickhouse_enabled, query_logs
from core.tenant_utils import resolve_tenant_id


def _pagination_from_request(request, default_page_size=50, max_page_size=200):
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max_page_size, max(1, int(request.query_params.get("page_size", default_page_size))))
    except (TypeError, ValueError):
        page_size = default_page_size
    return page, page_size


def _ch_filters_from_request(request, *, log_type: str, module_in=None):
    from core.audit_views import _parse_date

    filters = {"log_type": log_type}
    if module_in:
        filters["module_in"] = module_in

    tenant_id = request.query_params.get("tenant_id")
    if tenant_id:
        filters["tenant_id"] = tenant_id

    tenant_name = request.query_params.get("tenant_name")
    if tenant_name:
        filters["tenant_name"] = tenant_name

    module = request.query_params.get("module")
    if module:
        filters["module"] = module

    action = request.query_params.get("action")
    if action:
        filters["action"] = action

    search = request.query_params.get("search")
    if search:
        filters["search"] = search

    date_from = _parse_date(request.query_params.get("date_from"))
    if date_from:
        filters["date_from"] = date_from

    date_to = _parse_date(request.query_params.get("date_to"))
    if date_to:
        filters["date_to"] = date_to

    level = request.query_params.get("level")
    if level:
        filters["level"] = level

    service = request.query_params.get("service")
    if service:
        filters["service"] = service

    return filters


def fetch_logs_from_clickhouse(request, *, log_type: str, module_in=None, tenant_id=None):
    if not clickhouse_enabled():
        return None

    page, page_size = _pagination_from_request(request)
    filters = _ch_filters_from_request(request, log_type=log_type, module_in=module_in)
    if tenant_id and not filters.get("tenant_id"):
        filters["tenant_id"] = str(tenant_id)
    rows, total = query_logs(filters, page=page, page_size=page_size)

    if total == 0 and not rows:
        return None

    pages = max(1, (total + page_size - 1) // page_size)
    return rows, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
    }


def ch_row_to_login_session(row: dict) -> dict:
    meta = row.get("metadata") or {}
    return {
        "id": meta.get("session_id") or row.get("id"),
        "user": row.get("user_id"),
        "user_email": row.get("user_email"),
        "client_type": meta.get("client_type", "web"),
        "device_fingerprint": None,
        "ip_address": row.get("ip_address"),
        "user_agent": None,
        "location_city": meta.get("location_city"),
        "location_country": meta.get("location_country"),
        "login_method": meta.get("login_method", "password"),
        "is_revoked": bool(meta.get("is_revoked", False)),
        "created_at": row.get("created_at"),
        "tenant_id": row.get("tenant_id"),
        "tenant_name": row.get("tenant_name"),
    }


def effective_tenant_id(request, user):
    """Super Admin may pass ?tenant_id=; others use their own tenant."""
    from core.audit_views import _is_super_admin

    if _is_super_admin(user):
        override = request.query_params.get("tenant_id")
        if override:
            return override
    return resolve_tenant_id(user)
