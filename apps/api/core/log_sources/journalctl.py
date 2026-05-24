import json
import re
import shutil
import subprocess
from datetime import datetime, timezone

from django.conf import settings

from core.log_sources.base import LogEntry

LEVEL_PATTERN = re.compile(r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.I)


def _infer_level(message: str) -> str:
    match = LEVEL_PATTERN.search(message or "")
    if not match:
        return "INFO"
    level = match.group(1).upper()
    return "WARN" if level == "WARNING" else level


def _filter_entries(entries: list[LogEntry], level: str | None, search: str | None) -> list[LogEntry]:
    if level:
        level = level.upper()
        entries = [e for e in entries if e.level == level or (level == "WARN" and e.level == "WARNING")]
    if search:
        needle = search.lower()
        entries = [e for e in entries if needle in e.message.lower() or needle in e.raw.lower()]
    return entries


class JournalctlLogSource:
    def __init__(self):
        self.registry = getattr(settings, "LOG_SERVICE_REGISTRY", {})

    def list_services(self) -> list[str]:
        return list(self.registry.keys())

    def _unit(self, service: str) -> str | None:
        cfg = self.registry.get(service)
        return cfg.get("journal_unit") if cfg else None

    def tail(self, *, service=None, since=None, limit=500, level=None, search=None):
        services = [service] if service else self.list_services()
        entries: list[LogEntry] = []
        for svc in services:
            unit = self._unit(svc)
            if not unit:
                continue
            cmd = ["journalctl", "-u", unit, "-n", str(min(limit, 500)), "--no-pager", "-o", "json"]
            if since:
                cmd.extend(["--since", since])
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = payload.get("MESSAGE", "")
                ts = payload.get("__REALTIME_TIMESTAMP")
                timestamp = datetime.now(timezone.utc).isoformat()
                if ts:
                    try:
                        timestamp = datetime.fromtimestamp(int(ts) / 1_000_000, tz=timezone.utc).isoformat()
                    except (TypeError, ValueError):
                        pass
                priority = payload.get("PRIORITY")
                level_map = {
                    "0": "CRITICAL", "1": "CRITICAL", "2": "CRITICAL",
                    "3": "ERROR", "4": "WARN", "5": "INFO", "6": "INFO", "7": "DEBUG",
                }
                log_level = level_map.get(str(priority), _infer_level(message))
                entries.append(
                    LogEntry(
                        timestamp=timestamp,
                        level=log_level,
                        service=svc,
                        message=message,
                        raw=line,
                        metadata={"source": "journalctl", "unit": unit, "priority": priority},
                    )
                )
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return _filter_entries(entries[:limit], level, search)

    def service_status(self):
        statuses = []
        for svc in self.list_services():
            unit = self._unit(svc)
            state = "unknown"
            if unit and shutil.which("systemctl"):
                try:
                    result = subprocess.run(
                        ["systemctl", "is-active", unit],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    state = (result.stdout or "unknown").strip() or "unknown"
                except (subprocess.TimeoutExpired, OSError):
                    state = "unavailable"
            statuses.append({"service": svc, "state": state, "uptime": None, "backend": "journalctl"})
        return statuses
