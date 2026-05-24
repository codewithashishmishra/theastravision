import threading
import time
from typing import Callable

from core.activity_monitor import ActivityMonitor
from core.api_client import ApiClient, PlatformCooldownError
from core.crypto import encrypt_bytes, sha256
from core.gcm_crypto import screenshot_aad
from core.offline_queue import OfflineQueue
from core.screenshot import capture_all_monitors
from core.session_stats import SessionStats


class SessionManager:
    def __init__(
        self,
        client: ApiClient,
        device_uuid: str,
        policy: dict,
        on_stats_changed: Callable[[], None] | None = None,
        on_auto_pause: Callable[[], None] | None = None,
        on_cooldown: Callable[[int], None] | None = None,
    ):
        self.client = client
        self.device_uuid = device_uuid
        self.policy = policy or {}
        self.session_id = None
        self._running = False
        self._paused = False
        self._auto_pausing = False
        self._threads = []
        self.stats = SessionStats()
        self.activity = ActivityMonitor(auto_pause_seconds=60)
        self.activity.register_callbacks(
            on_activity=self._on_activity,
            on_spoof=self._on_spoof,
        )
        self.queue = OfflineQueue(refresh_token=client.refresh_token or "")
        self._on_stats_changed = on_stats_changed
        self._on_auto_pause = on_auto_pause
        self._on_cooldown = on_cooldown
        self._idle_logged = False
        self._server_idle_threshold = policy.get("idle_threshold_seconds", 300)

    @property
    def is_active(self) -> bool:
        return self._running and self.session_id is not None

    def _notify_stats(self):
        if self._on_stats_changed:
            self._on_stats_changed()

    def _notify_cooldown(self, retry_after: int = 300):
        if self._on_cooldown:
            self._on_cooldown(retry_after)

    def _on_activity(self):
        if self.stats._idle_tracking:
            self.stats.on_idle_end()
        self._notify_stats()

    def _on_spoof(self, spoof_type: str, detail: str):
        self.stats.on_spoof_flag(spoof_type, detail)
        self._notify_stats()

    def _trigger_auto_pause(self):
        if not self._running or self._paused or self._auto_pausing:
            return
        self._auto_pausing = True
        try:
            self.pause(reason="auto_idle")
            if self._on_auto_pause:
                self._on_auto_pause()
        finally:
            self._auto_pausing = False

    def start(self, task_title: str, task_description: str):
        if not self.client.data_key:
            raise RuntimeError("Missing encryption key — sign in again.")
        data = self.client.post(
            "/session/start/",
            json={
                "device_uuid": self.device_uuid,
                "task_title": task_title,
                "task_description": task_description,
            },
        )
        self.session_id = data.get("id")
        self.stats.on_start(task_title, task_description)
        self.queue.set_refresh_token(self.client.refresh_token or "")
        self._running = True
        self._paused = False
        self._notify_stats()
        self._threads = [
            threading.Thread(target=self._heartbeat_loop, daemon=True),
            threading.Thread(target=self._screenshot_loop, daemon=True),
            threading.Thread(target=self._idle_loop, daemon=True),
            threading.Thread(target=self._stats_tick_loop, daemon=True),
            threading.Thread(target=self._auto_pause_loop, daemon=True),
        ]
        for t in self._threads:
            t.start()

    def pause(self, reason: str = "manual"):
        if self._paused:
            return
        self._paused = True
        self.stats.on_pause(reason)
        self.client.post("/session/pause/", json={"reason": reason})
        self._notify_stats()

    def resume(self):
        if not self._paused:
            return
        self._paused = False
        self.activity.last_activity = time.time()
        self.stats.on_resume()
        self.client.post("/session/resume/", json={})
        self._notify_stats()

    def stop(self, graceful: bool = True) -> bool:
        self._running = False
        self.activity.stop()
        self.stats.on_stop()
        ok = True
        report = self.stats.build_day_report()
        if self.session_id and graceful:
            for attempt in range(3):
                try:
                    self.client.post("/session/report/", json=report)
                    break
                except Exception:
                    if attempt == 2:
                        ok = False
                    time.sleep(1)
        if self.session_id:
            try:
                self.client.post("/session/stop/", json={"report": report})
            except Exception:
                ok = False
        self._flush_queue()
        self.session_id = None
        self._notify_stats()
        return ok

    def _stats_tick_loop(self):
        while self._running:
            self.stats.tick()
            self._notify_stats()
            time.sleep(1)

    def _auto_pause_loop(self):
        while self._running:
            if not self._paused and self.activity.should_auto_pause():
                self._trigger_auto_pause()
            time.sleep(5)

    def _heartbeat_loop(self):
        interval = self.policy.get("heartbeat_interval_seconds", 60)
        while self._running:
            try:
                status = "paused" if self._paused else "active"
                self.client.post(
                    "/session/heartbeat/",
                    json={"app_status": status, "network_status": "online"},
                )
            except PlatformCooldownError as e:
                self._notify_cooldown(e.retry_after_seconds)
            except Exception:
                pass
            time.sleep(interval)

    def _screenshot_loop(self):
        interval = self.policy.get("screenshot_interval_seconds", 15)
        data_key = self.client.data_key
        while self._running:
            if self._paused:
                time.sleep(1)
                continue
            if not data_key:
                data_key = self.client.data_key
            if not data_key or not self.session_id:
                time.sleep(interval)
                continue
            try:
                for monitor, raw in capture_all_monitors():
                    checksum = sha256(raw)
                    aad = screenshot_aad(str(self.session_id), checksum, monitor)
                    gcm_blob = encrypt_bytes(raw, data_key, aad)
                    try:
                        self.client.post(
                            "/screenshot/upload/",
                            data={"checksum": checksum, "monitor_number": str(monitor)},
                            files={
                                "file": (
                                    f"{checksum}.aes-256-gcm.bin",
                                    gcm_blob,
                                    "application/octet-stream",
                                )
                            },
                        )
                    except PlatformCooldownError as e:
                        self.queue.enqueue("/screenshot/upload/", gcm_blob, checksum)
                        self._notify_cooldown(e.retry_after_seconds)
                    except Exception:
                        self.queue.enqueue("/screenshot/upload/", gcm_blob, checksum)
            except Exception:
                pass
            time.sleep(interval)

    def _idle_loop(self):
        while self._running:
            if self._paused:
                time.sleep(5)
                continue
            idle_sec = self.activity.idle_seconds()
            if idle_sec >= 60 and not self.stats._idle_tracking:
                self.stats.on_idle_start()
                self._notify_stats()
            elif idle_sec < 5 and self.stats._idle_tracking:
                self.stats.on_idle_end()
                self._notify_stats()
            if idle_sec >= self._server_idle_threshold and not self._idle_logged:
                try:
                    self.client.post(
                        "/idle-log/",
                        json={
                            "idle_start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "idle_duration": idle_sec,
                            "reason": "threshold_exceeded",
                        },
                    )
                except Exception:
                    pass
                self._idle_logged = True
            elif idle_sec < 30:
                self._idle_logged = False
            time.sleep(10)

    def _flush_queue(self):
        from core.gcm_crypto import decrypt_local

        refresh = self.client.refresh_token
        if not refresh:
            return
        for _ in range(3):
            pending = self.queue.pending()
            if not pending:
                break
            for row_id, endpoint, payload_enc, checksum in pending:
                try:
                    gcm_blob = decrypt_local(payload_enc, refresh, b"outbox")
                    self.client.post(
                        endpoint,
                        data={"checksum": checksum, "monitor_number": "1"},
                        files={
                            "file": (
                                f"{checksum}.aes-256-gcm.bin",
                                gcm_blob,
                                "application/octet-stream",
                            )
                        },
                    )
                    self.queue.mark_synced(row_id)
                except Exception:
                    return
