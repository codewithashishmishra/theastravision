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


class DockerLogSource:
    def __init__(self):
        self.project = getattr(settings, "LOG_DOCKER_COMPOSE_PROJECT", "theastravision")
        self.registry = getattr(settings, "LOG_SERVICE_REGISTRY", {})

    def list_services(self) -> list[str]:
        return list(self.registry.keys())

    def _container_name(self, service: str) -> str | None:
        cfg = self.registry.get(service)
        if not cfg:
            return None
        return cfg.get("docker_container") or f"{self.project}-{service}-1"

    def tail(self, *, service=None, since=None, limit=500, level=None, search=None):
        services = [service] if service else self.list_services()
        entries: list[LogEntry] = []
        for svc in services:
            container = self._container_name(svc)
            if not container:
                continue
            cmd = ["docker", "logs", "--tail", str(min(limit, 500)), container]
            if since:
                cmd[2:2] = ["--since", since]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                combined = (result.stdout or "") + (result.stderr or "")
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
            for line in combined.splitlines():
                if not line.strip():
                    continue
                entries.append(
                    LogEntry(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        level=_infer_level(line),
                        service=svc,
                        message=line.strip(),
                        raw=line,
                        metadata={"source": "docker", "container": container},
                    )
                )
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return _filter_entries(entries[:limit], level, search)

    def service_status(self):
        statuses = []
        for svc in self.list_services():
            container = self._container_name(svc)
            state = "unknown"
            uptime = None
            if container and shutil.which("docker"):
                try:
                    result = subprocess.run(
                        ["docker", "inspect", "-f", "{{.State.Status}}", container],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    state = (result.stdout or "unknown").strip() or "unknown"
                    started = subprocess.run(
                        ["docker", "inspect", "-f", "{{.State.StartedAt}}", container],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    uptime = (started.stdout or "").strip() or None
                except (subprocess.TimeoutExpired, OSError):
                    state = "unavailable"
            statuses.append({"service": svc, "state": state, "uptime": uptime, "backend": "docker"})
        return statuses
