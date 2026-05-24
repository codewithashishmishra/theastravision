#!/usr/bin/env python3
"""Aastraa WFH Tracker — visible, consent-based desktop tracking."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from core.api_client import ApiClient, ApiError
from core.auth import clear_session, load_session
from core.browser_login_worker import BrowserLoginWorker
from ui.consent_dialog import ConsentDialog
from ui.dashboard_window import DashboardWindow
from ui.login_window import LoginWindow
from ui.theme import APP_STYLESHEET
from ui.widgets import build_app_icon


def complete_session(client: ApiClient, login_data: dict, email: str, login_window: LoginWindow):
    """After auth: validate tracker profile, consent, open dashboard."""
    profile = client.get("/profile/")
    has_consent = profile.get("has_consent", False)
    if not has_consent:
        dlg = ConsentDialog(login_window)
        if dlg.exec() != ConsentDialog.DialogCode.Accepted:
            QMessageBox.warning(
                login_window,
                "Consent required",
                "Tracking cannot start without your consent.",
            )
            return None
        client.post("/consent/", json={"consent_type": "wfh_tracking_v1", "app_version": "1.0.0"})
        has_consent = True

    employee_name = (
        login_data.get("employee", {}).get("name")
        or profile.get("name")
        or email
    )
    policy = login_data.get("policy") or profile.get("policy") or {}

    login_window.hide()
    dashboard = DashboardWindow(client, employee_name, policy, has_consent)
    dashboard.show()
    dashboard.showMaximized()
    return dashboard


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Aastraa WFH Tracker")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app_icon = build_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    client = ApiClient()
    login = LoginWindow()
    dashboard = None
    worker: BrowserLoginWorker | None = None

    def open_dashboard(login_data: dict, email: str):
        nonlocal dashboard
        dashboard = complete_session(client, login_data, email, login)
        if dashboard:
            dashboard.logout_requested.connect(on_logout)

    def _finish_logout():
        nonlocal dashboard
        client.logout()
        clear_session()
        if dashboard:
            dashboard._allow_close = True
            dashboard.close()
            dashboard = None
        login.reset_login_button()
        login.show()

    def on_logout():
        nonlocal dashboard
        if dashboard and dashboard.session_manager and dashboard.session_manager.is_active:
            from PySide6.QtCore import Qt as QtCore

            dashboard.shutdown_complete.connect(_finish_logout, QtCore.ConnectionType.SingleShotConnection)
            dashboard._graceful_shutdown()
            return
        _finish_logout()

    def on_tokens(tokens: dict):
        nonlocal dashboard, worker
        try:
            email = tokens.get("email", "user")
            data = client.exchange_browser_token(tokens["access_token"])
            email = data.get("email") or email
            login_data = {
                "employee": data.get("employee"),
                "policy": data.get("policy"),
            }
            open_dashboard(login_data, email)
        except ApiError as e:
            login.show_error(str(e))
        except Exception as e:
            login.show_error(str(e))
        finally:
            if dashboard is None:
                login.reset_login_button()
            worker = None

    def on_browser_login_failed(msg: str):
        nonlocal worker
        login.show_error(msg)
        worker = None

    def on_browser_login():
        nonlocal worker
        if worker is not None and worker.isRunning():
            return
        worker = BrowserLoginWorker()
        worker.succeeded.connect(on_tokens)
        worker.failed.connect(on_browser_login_failed)
        worker.start()

    def try_restore_session():
        nonlocal dashboard
        stored = load_session()
        if not stored:
            return
        client.access_token = stored["access_token"]
        client.refresh_token = stored["refresh_token"]
        client.email = stored["email"]
        client.encryption_key_b64 = stored.get("encryption_key")
        if not client.refresh_access_token():
            client.access_token = stored["access_token"]
            if stored.get("encryption_key"):
                client.encryption_key_b64 = stored["encryption_key"]
        try:
            bootstrap = client.get("/auth/bootstrap/")
            login_data = {
                "employee": bootstrap.get("employee"),
                "policy": None,
            }
            profile = client.get("/profile/")
            login_data["policy"] = profile.get("policy")
            open_dashboard(login_data, stored["email"])
        except Exception:
            clear_session()
            client.access_token = None
            client.refresh_token = None

    login.browser_login_requested.connect(on_browser_login)
    login.show()
    try_restore_session()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
