from __future__ import annotations

import subprocess

from core.runtime.interface import ActiveWindowInfo, PlatformAgent
from core.screenshot import capture_primary_monitor


class LinuxPlatformAgent(PlatformAgent):
    def _run(self, cmd: list[str]) -> str:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=2)
            return (res.stdout or "").strip()
        except Exception:
            return ""

    def get_active_window(self) -> ActiveWindowInfo:
        title = ""
        app_name = "unknown"
        pid = None

        wid = self._run(["xdotool", "getactivewindow"])
        if wid:
            title = self._run(["xdotool", "getwindowname", wid])
            pid_raw = self._run(["xdotool", "getwindowpid", wid])
            if pid_raw.isdigit():
                pid = int(pid_raw)
                try:
                    import psutil

                    process_name = psutil.Process(pid).name() or ""
                    app_name = process_name.rsplit(".", 1)[0].lower() or "unknown"
                except Exception:
                    process_name = ""
            else:
                process_name = ""
        else:
            process_name = ""
            title = self._run(
                [
                    "gdbus",
                    "call",
                    "--session",
                    "--dest",
                    "org.freedesktop.portal.Desktop",
                    "--object-path",
                    "/org/freedesktop/portal/desktop",
                    "--method",
                    "org.freedesktop.DBus.Properties.Get",
                    "org.freedesktop.portal.Inhibit",
                    "version",
                ]
            )

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

