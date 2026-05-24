import threading
import time

from pynput import keyboard, mouse


class IdleMonitor:
    """Track last activity timestamp only — no keylogging."""

    def __init__(self, threshold_sec=300):
        self.last_activity = time.time()
        self.threshold = threshold_sec
        self._running = True
        mouse.Listener(on_move=self._bump, on_click=self._bump).start()
        keyboard.Listener(on_press=self._bump).start()

    def _bump(self, *args):
        self.last_activity = time.time()

    def is_idle(self) -> bool:
        return (time.time() - self.last_activity) >= self.threshold

    def idle_seconds(self) -> int:
        return int(time.time() - self.last_activity)
