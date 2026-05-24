"""Regional viewing timezone resolution for API responses."""

from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.cache import cache

from core.jurisdictions import JURISDICTION_CA, JURISDICTION_IN, JURISDICTION_US
from core.tenant_utils import get_employee_for_user

AUDIT_PATH_PREFIXES = (
    "/api/v1/audit/",
    "/api/v1/wfh/admin/audit-logs/",
)

JURISDICTION_DEFAULT_TIMEZONE = {
    JURISDICTION_IN: "Asia/Kolkata",
    JURISDICTION_US: "America/New_York",
    JURISDICTION_CA: "America/Toronto",
}

IP_GEO_CACHE_TTL = 3600

US_COUNTRY_NAMES = frozenset({"united states", "usa", "us"})
CA_COUNTRY_NAMES = frozenset({"canada", "ca"})


def is_audit_path(path: str) -> bool:
    for prefix in AUDIT_PATH_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def is_valid_timezone(name: str | None) -> bool:
    if not name or not str(name).strip():
        return False
    try:
        ZoneInfo(str(name).strip())
        return True
    except ZoneInfoNotFoundError:
        return False


def _zone(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def _resolve_jurisdiction(user) -> str:
    employee = get_employee_for_user(user)
    if employee and employee.payroll_jurisdiction:
        return employee.payroll_jurisdiction
    tenant = getattr(user, "tenant", None)
    if tenant and tenant.enabled_jurisdictions:
        return tenant.enabled_jurisdictions[0]
    return JURISDICTION_IN


def get_ip_timezone(ip: str | None) -> str | None:
    """Return a validated IANA timezone for an IP, using Django cache."""
    from core.utils import fetch_ip_geo

    if not ip:
        return None

    cache_key = f"ip_tz:{ip}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached else None

    geo = fetch_ip_geo(ip)
    tz_name = geo.get("timezone") if geo else None
    if tz_name and is_valid_timezone(tz_name):
        cache.set(cache_key, tz_name, IP_GEO_CACHE_TTL)
        return tz_name

    cache.set(cache_key, "", IP_GEO_CACHE_TTL)
    return None


def _ip_timezone_for_jurisdiction(ip: str | None, jurisdiction: str) -> str | None:
    from core.utils import fetch_ip_geo

    if not ip:
        return None

    geo = fetch_ip_geo(ip)
    if not geo:
        return get_ip_timezone(ip)

    country = (geo.get("country") or "").strip().lower()
    tz_name = geo.get("timezone")

    if jurisdiction == JURISDICTION_US and country in US_COUNTRY_NAMES:
        if tz_name and is_valid_timezone(tz_name):
            return tz_name
    if jurisdiction == JURISDICTION_CA and country in CA_COUNTRY_NAMES:
        if tz_name and is_valid_timezone(tz_name):
            return tz_name

    return get_ip_timezone(ip)


def resolve_viewing_timezone(request, user=None) -> ZoneInfo:
    """Resolve the timezone used for viewing API datetimes."""
    from core.utils import get_client_ip

    user = user or getattr(request, "user", None)
    jurisdiction = _resolve_jurisdiction(user) if user and user.is_authenticated else JURISDICTION_IN

    employee = get_employee_for_user(user) if user and user.is_authenticated else None
    if employee and employee.branch_id and employee.branch:
        branch_tz = employee.branch.timezone
        if branch_tz and branch_tz.strip().upper() != "UTC" and is_valid_timezone(branch_tz):
            return _zone(branch_tz.strip())

    ip = get_client_ip(request) if request else None
    ip_tz = _ip_timezone_for_jurisdiction(ip, jurisdiction)
    if ip_tz:
        return _zone(ip_tz)

    fallback = JURISDICTION_DEFAULT_TIMEZONE.get(jurisdiction, JURISDICTION_DEFAULT_TIMEZONE[JURISDICTION_IN])
    return _zone(fallback)


def activate_viewing_timezone(request, user=None) -> ZoneInfo:
    """Activate regional timezone on the current thread and attach to request."""
    from django.utils import timezone as dj_timezone

    tz = resolve_viewing_timezone(request, user=user)
    dj_timezone.activate(tz)
    if request is not None:
        request.viewing_timezone = str(tz)
        request._timezone_activated = True
    return tz
