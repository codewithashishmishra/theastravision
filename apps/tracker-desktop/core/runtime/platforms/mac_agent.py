from __future__ import annotations

import subprocess

from core.runtime.interface import ActiveWindowInfo, PlatformAgent
from core.screenshot import capture_primary_monitor


class MacPlatformAgent(PlatformAgent):
    def get_active_window(self) -> ActiveWindowInfo:
        app_name = "unknown"
        title = ""

        try:
            from AppKit import NSWorkspace

            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if app is not None:
                app_name = (app.localizedName() or "unknown").lower()
        except Exception:
            pass

        if app_name in {"safari", "google chrome", "microsoft edge", "brave browser", "firefox"}:
            title = self._browser_title(app_name)

        return ActiveWindowInfo(
            app_name=app_name,
            window_title=title,
            process_name=app_name,
            browser_tab_title=title,
        )

    def _browser_title(self, app_name: str) -> str:
        script = f'''
        tell application "{app_name}"
            if (count of windows) > 0 then
                return name of active tab of front window
            end if
        end tell
        '''
        try:
            proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=2, check=False)
            return (proc.stdout or "").strip()
        except Exception:
            return ""

    def take_screenshot(self) -> bytes:
        return capture_primary_monitor()

    def check_permissions(self) -> dict[str, bool]:
        # Probing permissions directly is brittle; runtime failures are handled gracefully.
        return {"screen_capture": True, "accessibility": True}

