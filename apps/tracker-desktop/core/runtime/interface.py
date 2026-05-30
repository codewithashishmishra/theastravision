from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ActiveWindowInfo:
    app_name: str
    window_title: str
    process_name: str = ""
    pid: int | None = None
    browser_tab_title: str = ""
    browser_url: str = ""


class PlatformAgent(ABC):
    @abstractmethod
    def get_active_window(self) -> ActiveWindowInfo:
        raise NotImplementedError

    @abstractmethod
    def take_screenshot(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def check_permissions(self) -> dict[str, bool]:
        raise NotImplementedError


@dataclass(slots=True)
class ScreenshotScheduleSlot:
    block_start: datetime
    block_end: datetime
    capture_at: datetime

