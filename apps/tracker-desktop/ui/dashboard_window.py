import uuid

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.session_manager import SessionManager
from ui.session_stats_panel import SessionStatsPanel
from ui.start_work_dialog import StartWorkDialog
from ui.bug_report_dialog import BugReportDialog
from ui.theme import COLORS
from ui.widgets import apply_window_icon, brand_logo_label


class DashboardWindow(QMainWindow):
    logout_requested = Signal()
    shutdown_complete = Signal(bool)

    def __init__(self, client, employee_name: str, policy: dict, has_consent: bool):
        super().__init__()
        self.client = client
        self.policy = policy
        self.device_uuid = str(uuid.uuid4())
        self.session_manager: SessionManager | None = None
        self._current_task_title = ""
        self._has_consent = has_consent
        self._allow_close = False
        self._shutting_down = False

        self.setWindowTitle("Aastraa WFH Tracker")
        self.setMinimumSize(1200, 700)
        apply_window_icon(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel(employee_name))
        self.stats_panel = SessionStatsPanel(self.client)
        splitter.addWidget(self.stats_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        splitter.setSizes([480, 720])

        self.setCentralWidget(splitter)
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Consent-based · visible tracking · approved WFH only")

        self._refresh_wfh_status()
        self.register_device()

    def _build_left_panel(self, employee_name: str) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.addWidget(brand_logo_label(56, 56))
        title_col = QVBoxLayout()
        greet = QLabel(f"Hello, {employee_name}")
        greet.setObjectName("heading")
        title_col.addWidget(greet)
        sub = QLabel("WFH productivity tracker")
        sub.setObjectName("subtitle")
        title_col.addWidget(sub)
        header_layout.addLayout(title_col, stretch=1)
        layout.addWidget(header_card)

        self.status_banner = QLabel("NOT TRACKING")
        self.status_banner.setObjectName("statusBanner")
        self.status_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_banner.setMinimumHeight(72)
        self._set_banner_idle()
        layout.addWidget(self.status_banner)

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)
        self.wfh_label = QLabel("Checking WFH approval…")
        self.wfh_label.setObjectName("subtitle")
        self.wfh_label.setWordWrap(True)
        info_layout.addWidget(self.wfh_label)
        self.task_label = QLabel("")
        self.task_label.setObjectName("info")
        self.task_label.setWordWrap(True)
        self.task_label.hide()
        info_layout.addWidget(self.task_label)
        self.sync_label = QLabel("Sync: ready")
        self.sync_label.setObjectName("info")
        info_layout.addWidget(self.sync_label)
        layout.addWidget(info_card)

        footer = QLabel("© theastravision.com")
        footer.setObjectName("subtitle")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        self.start_btn = QPushButton("Start Work")
        self.start_btn.setObjectName("primary")
        self.start_btn.setMinimumHeight(48)
        self.start_btn.clicked.connect(self.start_tracking)
        layout.addWidget(self.start_btn)

        row = QHBoxLayout()
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("secondary")
        self.pause_btn.setMinimumHeight(44)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_tracking)
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setObjectName("primary")
        self.resume_btn.setMinimumHeight(44)
        self.resume_btn.setEnabled(False)
        self.resume_btn.hide()
        self.resume_btn.clicked.connect(self.resume_tracking)
        self.stop_btn = QPushButton("Stop Work")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_tracking)
        row.addWidget(self.pause_btn)
        row.addWidget(self.resume_btn)
        row.addWidget(self.stop_btn)
        layout.addLayout(row)

        note = QLabel("This app never runs in the background hidden. Status stays visible on screen.")
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.logout_btn = QPushButton("Log out")
        self.logout_btn.setObjectName("secondary")
        self.logout_btn.setMinimumHeight(40)
        self.logout_btn.clicked.connect(self._on_logout_clicked)
        layout.addWidget(self.logout_btn)
        
        self.bug_btn = QPushButton("Report a Bug")
        self.bug_btn.setObjectName("secondary")
        self.bug_btn.setMinimumHeight(40)
        self.bug_btn.clicked.connect(self._on_bug_clicked)
        layout.addWidget(self.bug_btn)

        session_note = QLabel(
            ""
        )
        session_note.setObjectName("subtitle")
        session_note.setWordWrap(True)
        layout.addWidget(session_note)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _refresh_stats_panel(self):
        if self.session_manager:
            self.stats_panel.update_from_stats(self.session_manager.stats)

    def _set_banner_idle(self):
        self.status_banner.setText("NOT TRACKING")
        self.status_banner.setStyleSheet(
            f"background-color: {COLORS['bg_input']}; color: {COLORS['text_muted']}; "
            f"border: 2px dashed {COLORS['border']}; border-radius: 12px; padding: 20px;"
        )

    def _set_banner_active(self):
        self.status_banner.setText("TRACKING ACTIVE")
        self.status_banner.setStyleSheet(
            f"background-color: {COLORS['success']}; color: white; border-radius: 12px; padding: 20px;"
        )

    def _set_banner_paused(self):
        self.status_banner.setText("TRACKING PAUSED")
        self.status_banner.setStyleSheet(
            f"background-color: {COLORS['warning']}; color: #1e293b; border-radius: 12px; padding: 20px;"
        )

    def _set_tracking_controls_active(self):
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.pause_btn.show()
        self.resume_btn.setEnabled(False)
        self.resume_btn.hide()
        self.stop_btn.setEnabled(True)

    def _set_tracking_controls_paused(self):
        self.start_btn.setEnabled(False)
        self.pause_btn.hide()
        self.resume_btn.setEnabled(True)
        self.resume_btn.show()
        self.stop_btn.setEnabled(True)

    def _set_tracking_controls_idle(self):
        self.start_btn.setEnabled(self._has_consent)
        self.pause_btn.setEnabled(False)
        self.pause_btn.show()
        self.resume_btn.hide()
        self.stop_btn.setEnabled(False)

    def _show_task_summary(self, title: str, description: str):
        self._current_task_title = title
        preview = description if len(description) <= 120 else f"{description[:117]}…"
        self.task_label.setText(f"<b>Today's task:</b> {title}<br>{preview}")
        self.task_label.show()

    def closeEvent(self, event):
        if self._allow_close:
            event.accept()
            return
        if self.session_manager and self.session_manager.is_active:
            event.ignore()
            self._graceful_shutdown(close_after=True)
            return
        event.accept()

    def _graceful_shutdown(self, close_after: bool = False):
        if self._shutting_down:
            return
        if not self.session_manager or not self.session_manager.is_active:
            self.shutdown_complete.emit(True)
            if close_after:
                self._allow_close = True
                self.close()
            return

        self._shutting_down = True
        dlg = QProgressDialog("Syncing today's report…", None, 0, 0, self)
        dlg.setWindowTitle("Please wait")
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.show()

        ok = self.session_manager.stop(graceful=True)
        dlg.close()
        self.session_manager = None
        self._shutting_down = False
        self._set_banner_idle()
        self._set_tracking_controls_idle()
        self.task_label.hide()
        self._refresh_stats_panel()
        self.sync_label.setText("Session ended · report synced" if ok else "Session ended · sync incomplete")
        self.statusBar().showMessage("Tracking stopped")

        if not ok:
            retry = QMessageBox.warning(
                self,
                "Sync failed",
                "Could not upload the full-day report. Retry before closing?",
                QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Ignore,
            )
            if retry == QMessageBox.StandardButton.Retry:
                return
        self.shutdown_complete.emit(ok)
        if close_after:
            self._allow_close = True
            self.close()

    def _on_bug_clicked(self):
        dlg = BugReportDialog(self, self.client)
        dlg.exec()

    def _on_logout_clicked(self):
        if self.session_manager and self.session_manager.is_active:
            reply = QMessageBox.question(
                self,
                "Log out",
                "An active session will sync its report before logout. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            from PySide6.QtCore import Qt as QtCore

            self.shutdown_complete.connect(
                lambda _ok: self.logout_requested.emit(),
                QtCore.ConnectionType.SingleShotConnection,
            )
            self._graceful_shutdown()
            return
        reply = QMessageBox.question(
            self,
            "Log out",
            "Sign out of the WFH Tracker on this device?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()

    def register_device(self):
        import platform

        try:
            self.client.post(
                "/device/register/",
                json={
                    "device_uuid": self.device_uuid,
                    "device_name": platform.node(),
                    "os_name": platform.system(),
                    "os_version": platform.version(),
                    "app_version": "1.0.0",
                },
            )
            self.sync_label.setText("Device registered · ready to sync")
        except Exception as e:
            self.sync_label.setText(f"Sync issue: {e}")

    def _refresh_wfh_status(self):
        try:
            st = self.client.get("/approved-wfh-status/")
            if st.get("can_track"):
                self.wfh_label.setText("WFH is approved for today. You can start tracking when ready.")
                if not self.session_manager:
                    self.start_btn.setEnabled(self._has_consent)
            else:
                self.wfh_label.setText(
                    "No approved WFH for today.\n"
                    "Submit a request in HRMS and get manager/HR approval first."
                )
                self.start_btn.setEnabled(False)
        except Exception as e:
            self.wfh_label.setText(f"Could not verify WFH status: {e}")

    def start_tracking(self):
        if not self._has_consent:
            return
        dlg = StartWorkDialog(self)
        if dlg.exec() != StartWorkDialog.DialogCode.Accepted:
            return
        title = dlg.task_title()
        description = dlg.task_description()
        self.session_manager = SessionManager(
            self.client,
            self.device_uuid,
            self.policy,
            on_stats_changed=self._refresh_stats_panel,
            on_auto_pause=self._on_auto_pause,
            on_cooldown=self._on_platform_cooldown,
        )
        try:
            self.session_manager.start(title, description)
            self._show_task_summary(title, description)
            self._set_banner_active()
            self._set_tracking_controls_active()
            self.sync_label.setText("Session active · syncing")
            self._refresh_stats_panel()
            self.statusBar().showMessage("Tracking active — visible at all times")
        except Exception as e:
            self.session_manager = None
            QMessageBox.warning(self, "Could not start", str(e))

    def _on_auto_pause(self):
        self._set_banner_paused()
        self._set_tracking_controls_paused()
        self.sync_label.setText("Auto-paused · no input for 1 minute")
        self.statusBar().showMessage("Auto-paused — click Resume to continue")

    def _on_platform_cooldown(self, retry_after_seconds: int):
        minutes = max(1, (retry_after_seconds + 59) // 60)
        self.sync_label.setText(
            f"Server cooling down (~{minutes} min). Data queued locally — will sync when back up."
        )
        self.statusBar().showMessage(
            "System is temporarily down for maintenance. Your tracking data is saved locally."
        )

    def pause_tracking(self):
        if not self.session_manager:
            return
        try:
            self.session_manager.pause(reason="manual")
            self._set_banner_paused()
            self._set_tracking_controls_paused()
            self.sync_label.setText("Session paused · screenshots stopped")
        except Exception as e:
            self.statusBar().showMessage(str(e))

    def resume_tracking(self):
        if not self.session_manager:
            return
        try:
            self.session_manager.resume()
            self._set_banner_active()
            self._set_tracking_controls_active()
            self.sync_label.setText("Session active · syncing")
        except Exception as e:
            QMessageBox.warning(self, "Could not resume", str(e))

    def stop_tracking(self):
        if not self.session_manager:
            return
        self._graceful_shutdown(close_after=False)
