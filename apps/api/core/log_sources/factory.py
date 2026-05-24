import os
import shutil

from django.conf import settings

from core.log_sources.docker import DockerLogSource
from core.log_sources.journalctl import JournalctlLogSource


def get_log_source():
    mode = getattr(settings, "LOG_SOURCE", "auto")
    if mode == "docker":
        return DockerLogSource()
    if mode == "journalctl":
        return JournalctlLogSource()
    if shutil.which("docker") and not os.path.exists("/.dockerenv"):
        return DockerLogSource()
    if shutil.which("journalctl"):
        return JournalctlLogSource()
    return DockerLogSource()
