import os
import shutil

from django.conf import settings

from core.log_sources.docker import DockerLogSource
from core.log_sources.journalctl import JournalctlLogSource
from core.log_sources.local_dev import LocalDevLogSource


def get_log_source():
    mode = getattr(settings, "LOG_SOURCE", "auto").lower()
    if mode == "local":
        return LocalDevLogSource()
    if mode == "docker":
        return DockerLogSource()
    if mode == "journalctl":
        return JournalctlLogSource()
    if getattr(settings, "DEBUG", False):
        return LocalDevLogSource()
    if shutil.which("docker") and not os.path.exists("/.dockerenv"):
        return DockerLogSource()
    if shutil.which("journalctl"):
        return JournalctlLogSource()
    return LocalDevLogSource()
