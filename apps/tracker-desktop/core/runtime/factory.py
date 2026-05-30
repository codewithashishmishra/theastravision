from __future__ import annotations

import platform

from core.runtime.interface import PlatformAgent
from core.runtime.platforms.linux_agent import LinuxPlatformAgent
from core.runtime.platforms.mac_agent import MacPlatformAgent
from core.runtime.platforms.windows_agent import WindowsPlatformAgent


def build_platform_agent() -> PlatformAgent:
    system = platform.system().lower()
    if system == "windows":
        return WindowsPlatformAgent()
    if system == "darwin":
        return MacPlatformAgent()
    return LinuxPlatformAgent()

