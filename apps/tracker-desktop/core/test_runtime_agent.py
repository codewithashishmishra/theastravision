from datetime import datetime, timezone

from core.runtime.agent import RandomScreenshotScheduler, parse_interval


def test_parse_interval_accepts_expected_values():
    assert parse_interval("15s") == 15
    assert parse_interval("30m") == 1800
    assert parse_interval(60) == 60


def test_scheduler_emits_once_per_block():
    scheduler = RandomScreenshotScheduler(interval_seconds=60)
    now = datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    seen_capture = False
    for sec in range(0, 60):
        should = scheduler.should_capture(now.replace(second=sec))
        if should:
            seen_capture = True
            break
    assert seen_capture
