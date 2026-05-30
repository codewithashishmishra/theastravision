from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.runtime.interface import ScreenshotScheduleSlot

ALLOWED_INTERVALS_SECONDS = {
    "15s": 15,
    "30s": 30,
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "45m": 2700,
}


def parse_interval(value: str | int) -> int:
    if isinstance(value, int):
        if value in ALLOWED_INTERVALS_SECONDS.values():
            return value
        raise ValueError("Unsupported numeric screenshot interval.")
    if value not in ALLOWED_INTERVALS_SECONDS:
        raise ValueError(f"Unsupported screenshot interval '{value}'.")
    return ALLOWED_INTERVALS_SECONDS[value]


@dataclass
class RandomScreenshotScheduler:
    interval_seconds: int
    _current: ScreenshotScheduleSlot | None = None

    def __post_init__(self) -> None:
        if self.interval_seconds not in ALLOWED_INTERVALS_SECONDS.values():
            raise ValueError("Unsupported screenshot interval.")

    def _build_slot(self, now: datetime) -> ScreenshotScheduleSlot:
        now_epoch = int(now.timestamp())
        block_start_epoch = (now_epoch // self.interval_seconds) * self.interval_seconds
        block_start = datetime.fromtimestamp(block_start_epoch, tz=timezone.utc)
        block_end = block_start + timedelta(seconds=self.interval_seconds)
        capture_offset = random.randint(0, self.interval_seconds - 1)
        capture_at = block_start + timedelta(seconds=capture_offset)
        return ScreenshotScheduleSlot(block_start=block_start, block_end=block_end, capture_at=capture_at)

    def should_capture(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if self._current is None or now >= self._current.block_end:
            self._current = self._build_slot(now)
        return now >= self._current.capture_at

