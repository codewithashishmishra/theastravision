"""Platform-wide settings stored in EnvConfiguration (Super Admin)."""

from django.conf import settings

MODULE_PLATFORM_UTILIZATION = "PLATFORM_UTILIZATION"

_DEFAULTS = {
    "enabled": True,
    "cpu_threshold_percent": 80,
    "ram_threshold_percent": 80,
    "cooldown_duration_seconds": 300,
    "sample_interval_seconds": 30,
    "super_admin_bypass": False,
    "cooldown_message": "System is cooling down. Please retry in about 5 minutes.",
}


def _settings_defaults() -> dict:
    return {
        "enabled": True,
        "cpu_threshold_percent": getattr(settings, "UTIL_COOLDOWN_CPU_THRESHOLD", 80),
        "ram_threshold_percent": getattr(settings, "UTIL_COOLDOWN_RAM_THRESHOLD", 80),
        "cooldown_duration_seconds": getattr(settings, "UTIL_COOLDOWN_DURATION_SECONDS", 300),
        "sample_interval_seconds": getattr(settings, "UTIL_SAMPLE_INTERVAL_SECONDS", 30),
        "super_admin_bypass": getattr(settings, "UTIL_COOLDOWN_SUPER_ADMIN_BYPASS", False),
        "cooldown_message": "System is cooling down. Please retry in about 5 minutes.",
    }


def get_platform_utilization_config() -> dict:
    from core.models import EnvConfiguration

    merged = {**_settings_defaults(), **_DEFAULTS}
    db_config = EnvConfiguration.get_cached_config(MODULE_PLATFORM_UTILIZATION)
    if db_config:
        merged.update(db_config)
    return merged


def _as_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _as_bool(value, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value) if value is not None else fallback


def utilization_enabled() -> bool:
    return _as_bool(get_platform_utilization_config().get("enabled"), True)


def cpu_threshold() -> int:
    cfg = get_platform_utilization_config()
    return _as_int(cfg.get("cpu_threshold_percent"), 80)


def ram_threshold() -> int:
    cfg = get_platform_utilization_config()
    return _as_int(cfg.get("ram_threshold_percent"), 80)


def cooldown_duration_seconds() -> int:
    cfg = get_platform_utilization_config()
    return _as_int(cfg.get("cooldown_duration_seconds"), 300)


def super_admin_bypass_enabled() -> bool:
    cfg = get_platform_utilization_config()
    return _as_bool(cfg.get("super_admin_bypass"), False)


def cooldown_message() -> str:
    cfg = get_platform_utilization_config()
    return str(
        cfg.get("cooldown_message")
        or "System is cooling down. Please retry in about 5 minutes."
    )
