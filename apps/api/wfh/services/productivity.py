import re
from urllib.parse import urlparse

from wfh.models import ProductivityRule


def _target_value(target_type: str, app_name: str, tab_title: str, browser_url: str) -> str:
    if target_type == ProductivityRule.TARGET_APP:
        return (app_name or "").strip().lower()
    if target_type == ProductivityRule.TARGET_TAB:
        return (tab_title or "").strip().lower()
    if target_type == ProductivityRule.TARGET_DOMAIN:
        host = urlparse(browser_url or "").hostname or ""
        return host.lower()
    return ""


def classify_focus(tenant_id, app_name: str, tab_title: str, browser_url: str = ""):
    value_cache: dict[str, str] = {}
    rules = ProductivityRule.objects.filter(tenant_id=tenant_id, is_active=True).order_by("created_at")
    for rule in rules:
        probe = value_cache.get(rule.target_type)
        if probe is None:
            probe = _target_value(rule.target_type, app_name, tab_title, browser_url)
            value_cache[rule.target_type] = probe
        if not probe:
            continue
        pattern = (rule.pattern or "").strip().lower()
        if not pattern:
            continue
        matched = False
        if rule.match_type == ProductivityRule.MATCH_EXACT:
            matched = probe == pattern
        else:
            try:
                matched = re.search(pattern, probe, flags=re.IGNORECASE) is not None
            except re.error:
                matched = False
        if matched:
            return rule.is_productive, rule
    return False, None

