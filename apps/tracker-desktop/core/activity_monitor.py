"""Activity patterns for auto-pause and spoof detection (no key content stored)."""

import statistics
import threading
import time
from collections import deque

from pynput import keyboard, mouse

AUTO_PAUSE_SECONDS = 60
SPOOF_SCROLL_ONLY_SECONDS = 45
REPEATED_KEY_WINDOW = 30
REPEATED_KEY_RATIO = 0.85
SYNTHETIC_MOUSE_MOVES = 50
SYNTHETIC_MOUSE_STDDEV_MS = 15.0


class ActivityMonitor:
    def __init__(self, auto_pause_seconds=AUTO_PAUSE_SECONDS):
        self.auto_pause_seconds = auto_pause_seconds
        self.last_activity = time.time()
        self._last_key_time = 0.0
        self._key_ring: deque = deque(maxlen=REPEATED_KEY_WINDOW)
        self._move_times: deque = deque(maxlen=SYNTHETIC_MOUSE_MOVES)
        self._last_move_pos = None
        self._last_move_ts = 0.0
        self._scroll_only_since = None
        self._running = True
        self._lock = threading.Lock()
        self._on_activity = None
        self._on_auto_pause = None
        self._on_spoof = None
        self._spoof_cooldown: dict[str, float] = {}

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._bump,
            on_scroll=self._on_scroll,
        )
        self._key_listener = keyboard.Listener(on_press=self._on_key)
        self._mouse_listener.start()
        self._key_listener.start()

    def register_callbacks(self, on_activity=None, on_auto_pause=None, on_spoof=None):
        self._on_activity = on_activity
        self._on_auto_pause = on_auto_pause
        self._on_spoof = on_spoof

    def stop(self):
        self._running = False
        try:
            self._mouse_listener.stop()
        except Exception:
            pass
        try:
            self._key_listener.stop()
        except Exception:
            pass

    def _bump(self, *args):
        with self._lock:
            self.last_activity = time.time()
            self._scroll_only_since = None
        if self._on_activity:
            self._on_activity()

    def _on_key(self, key):
        code = str(key)
        now = time.time()
        with self._lock:
            self.last_activity = now
            self._last_key_time = now
            self._scroll_only_since = None
            self._key_ring.append(code)
        if self._on_activity:
            self._on_activity()
        self._check_repeated_key()

    def _on_scroll(self, x, y, dx, dy):
        now = time.time()
        with self._lock:
            self.last_activity = now
            if self._last_key_time == 0 or (now - self._last_key_time) > 5:
                if self._scroll_only_since is None:
                    self._scroll_only_since = now
        if self._on_activity:
            self._on_activity()
        self._check_scroll_only()

    def _on_mouse_move(self, x, y):
        now = time.time()
        with self._lock:
            self.last_activity = now
            if self._last_move_ts:
                self._move_times.append((now - self._last_move_ts) * 1000)
            self._last_move_ts = now
            self._last_move_pos = (x, y)
        if self._on_activity:
            self._on_activity()
        self._check_synthetic_mouse()

    def idle_seconds(self) -> int:
        return int(time.time() - self.last_activity)

    def should_auto_pause(self) -> bool:
        return self.idle_seconds() >= self.auto_pause_seconds

    def _emit_spoof(self, spoof_type: str, detail: str):
        now = time.time()
        if now - self._spoof_cooldown.get(spoof_type, 0) < 120:
            return
        self._spoof_cooldown[spoof_type] = now
        if self._on_spoof:
            self._on_spoof(spoof_type, detail)

    def _check_repeated_key(self):
        with self._lock:
            if len(self._key_ring) < 15:
                return
            keys = list(self._key_ring)
        most = max(set(keys), key=keys.count)
        ratio = keys.count(most) / len(keys)
        if ratio >= REPEATED_KEY_RATIO:
            self._emit_spoof("repeated_key", f"Key {most} repeated {ratio:.0%} of recent presses")

    def _check_scroll_only(self):
        with self._lock:
            if self._scroll_only_since is None:
                return
            elapsed = time.time() - self._scroll_only_since
        if elapsed >= SPOOF_SCROLL_ONLY_SECONDS:
            self._emit_spoof("scroll_only", "Scroll/wheel without keyboard activity")
            with self._lock:
                self._scroll_only_since = time.time()

    def _check_synthetic_mouse(self):
        with self._lock:
            intervals = list(self._move_times)
        if len(intervals) < SYNTHETIC_MOUSE_MOVES:
            return
        try:
            stdev = statistics.pstdev(intervals)
        except statistics.StatisticsError:
            return
        if stdev < SYNTHETIC_MOUSE_STDDEV_MS:
            self._emit_spoof(
                "synthetic_mouse",
                f"Mouse moves at near-fixed intervals (stdev={stdev:.1f}ms)",
            )
