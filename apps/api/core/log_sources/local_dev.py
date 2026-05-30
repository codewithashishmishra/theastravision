"""Local process health checks for native Windows/macOS dev (start_services.py)."""

from __future__ import annotations

import socket

from core.log_sources.base import LogEntry

# service label -> (host, port)
LOCAL_SERVICES = {
    "api": ("127.0.0.1", 8000),
    "ai-service": ("127.0.0.1", 8001),
    "admin-web": ("127.0.0.1", 3000),
    "redis": ("127.0.0.1", 6379),
}


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class LocalDevLogSource:
    def list_services(self) -> list[str]:
        return list(LOCAL_SERVICES.keys())

    def tail(
        self,
        *,
        service: str | None = None,
        since: str | None = None,
        limit: int = 500,
        level: str | None = None,
        search: str | None = None,
    ) -> list[LogEntry]:
        return []

    def service_status(self) -> list[dict]:
        statuses = []
        for svc, (host, port) in LOCAL_SERVICES.items():
            up = _port_open(host, port)
            statuses.append(
                {
                    "service": svc,
                    "state": "running" if up else "down",
                    "uptime": None,
                    "backend": "local",
                }
            )
        return statuses
