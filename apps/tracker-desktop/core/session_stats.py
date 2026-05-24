"""Local session timeline and duration counters for the dashboard."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SessionState(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"


@dataclass
class StatsEvent:
    event_type: str
    at: datetime
    detail: str
    active_sec: int
    idle_sec: int
    paused_sec: int
    metadata: dict = field(default_factory=dict)


class SessionStats:
    def __init__(self):
        self.state = SessionState.IDLE
        self.task_title = ""
        self.task_description = ""
        self.active_sec = 0
        self.idle_sec = 0
        self.paused_sec = 0
        self.spoof_flags: list[str] = []
        self._events: list[StatsEvent] = []
        self._state_started = datetime.now(timezone.utc)
        self._idle_tracking = False

    def _tick_state(self):
        now = datetime.now(timezone.utc)
        elapsed = int((now - self._state_started).total_seconds())
        if elapsed <= 0:
            return
        if self.state == SessionState.ACTIVE:
            if self._idle_tracking:
                self.idle_sec += elapsed
            else:
                self.active_sec += elapsed
        elif self.state == SessionState.PAUSED:
            self.paused_sec += elapsed
        self._state_started = now

    def _set_state(self, state: SessionState):
        self._tick_state()
        self.state = state
        self._state_started = datetime.now(timezone.utc)

    def _append(self, event_type: str, detail: str, metadata=None):
        self._tick_state()
        ev = StatsEvent(
            event_type=event_type,
            at=datetime.now(timezone.utc),
            detail=detail,
            active_sec=self.active_sec,
            idle_sec=self.idle_sec,
            paused_sec=self.paused_sec,
            metadata=metadata or {},
        )
        self._events.append(ev)
        return ev

    def on_start(self, title: str, description: str):
        self.task_title = title
        self.task_description = description
        self.active_sec = self.idle_sec = self.paused_sec = 0
        self.spoof_flags = []
        self._events.clear()
        self._idle_tracking = False
        self._set_state(SessionState.ACTIVE)
        self._append("session_start", title, {"task_description": description})

    def on_pause(self, reason: str = "manual"):
        self._idle_tracking = False
        self._set_state(SessionState.PAUSED)
        et = "auto_pause" if reason == "auto_idle" else "pause"
        self._append(et, reason)

    def on_resume(self):
        self._set_state(SessionState.ACTIVE)
        self._append("resume", "Tracking resumed")

    def on_idle_start(self):
        if self.state != SessionState.ACTIVE or self._idle_tracking:
            return
        self._tick_state()
        self._idle_tracking = True
        self._append("idle_start", "No keyboard/mouse activity")

    def on_idle_end(self):
        if not self._idle_tracking:
            return
        self._tick_state()
        self._idle_tracking = False
        self._append("idle_end", "Activity resumed")

    def on_spoof_flag(self, spoof_type: str, detail: str):
        if spoof_type not in self.spoof_flags:
            self.spoof_flags.append(spoof_type)
        self._append("spoof_detected", detail, {"spoof_type": spoof_type})

    def on_stop(self):
        self._tick_state()
        self._append("session_stop", "Work session ended")
        self.state = SessionState.IDLE

    def tick(self):
        """Call periodically to advance duration counters."""
        self._tick_state()

    def format_hours(self, seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h:
            return f"{h}h {m}m {s}s"
        if m:
            return f"{m}m {s}s"
        return f"{s}s"

    def events_for_table(self) -> list[dict]:
        self._tick_state()
        rows = []
        for ev in self._events:
            rows.append(
                {
                    "time": ev.at.strftime("%H:%M:%S"),
                    "event": ev.event_type.replace("_", " ").title(),
                    "active": self.format_hours(ev.active_sec),
                    "idle": self.format_hours(ev.idle_sec),
                    "paused": self.format_hours(ev.paused_sec),
                    "detail": ev.detail,
                }
            )
        return rows

    def build_day_report(self) -> dict:
        self._tick_state()
        return {
            "task_title": self.task_title,
            "task_description": self.task_description,
            "totals": {
                "active": self.active_sec,
                "idle": self.idle_sec,
                "paused": self.paused_sec,
                "active_sec": self.active_sec,
                "idle_sec": self.idle_sec,
                "paused_sec": self.paused_sec,
            },
            "spoof_flags": list(self.spoof_flags),
            "events": [
                {
                    "event_type": ev.event_type,
                    "occurred_at": ev.at.isoformat().replace("+00:00", "Z"),
                    "detail": ev.detail,
                    "metadata": ev.metadata,
                }
                for ev in self._events
            ],
        }
