"""Background thread for browser SSO so the Qt UI stays responsive."""

from PySide6.QtCore import QThread, Signal

from core.browser_auth import login_via_browser
from core.config import WEB_LOGIN_URL


class BrowserLoginWorker(QThread):
    succeeded = Signal(dict)
    failed = Signal(str)

    def run(self):
        try:
            tokens = login_via_browser(WEB_LOGIN_URL)
            self.succeeded.emit(tokens)
        except Exception as e:
            self.failed.emit(str(e))
