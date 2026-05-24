from dataclasses import dataclass, asdict
from typing import Protocol


@dataclass
class LogEntry:
    timestamp: str
    level: str
    service: str
    message: str
    raw: str
    metadata: dict

    def to_dict(self):
        return asdict(self)


class LogSource(Protocol):
    def tail(
        self,
        *,
        service: str | None = None,
        since: str | None = None,
        limit: int = 500,
        level: str | None = None,
        search: str | None = None,
    ) -> list[LogEntry]:
        ...

    def list_services(self) -> list[str]:
        ...

    def service_status(self) -> list[dict]:
        ...
