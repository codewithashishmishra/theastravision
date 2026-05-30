from __future__ import annotations

from core.runtime.interface import ActiveWindowInfo, PlatformAgent
from core.screenshot import capture_primary_monitor


class WindowsPlatformAgent(PlatformAgent):
    def get_active_window(self) -> ActiveWindowInfo:
        try:
            import win32gui
            import win32process
        except Exception:
            return ActiveWindowInfo(app_name="unknown", window_title="")

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) or ""
        pid = None
        process_name = ""
        app_name = "unknown"
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid:
                import psutil

                proc = psutil.Process(pid)
                process_name = proc.name() or ""
                app_name = process_name.rsplit(".", 1)[0].lower() or "unknown"
        except Exception:
            pass

        return ActiveWindowInfo(
            app_name=app_name,
            window_title=title,
            process_name=process_name,
            pid=pid,
            browser_tab_title=title,
        )

    def take_screenshot(self) -> bytes:
        return capture_primary_monitor()

    def check_permissions(self) -> dict[str, bool]:
        return {"screen_capture": True, "accessibility": True}

