from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
)

from ui.widgets import apply_window_icon, brand_logo_label


class LoginWindow(QWidget):
    browser_login_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aastraa WFH Tracker")
        self.setFixedSize(440, 540)
        apply_window_icon(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(16)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        card_layout.addWidget(brand_logo_label(220, 80), alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("Aastraa WFH Tracker")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel(
            "Sign in with your HRMS account.\n"
            "Your browser will open to complete login."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        self.login_btn = QPushButton("Sign in with HRMS")
        self.login_btn.setObjectName("primary")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setMinimumHeight(48)
        self.login_btn.clicked.connect(self._start_browser_login)
        card_layout.addWidget(self.login_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("info")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        card_layout.addWidget(self.status_label)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        root.addWidget(card)

        hint = QLabel(
            "Visible tracking · consent required\nApproved WFH sessions only"
        )
        hint.setObjectName("subtitle")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        hint.setContentsMargins(8, 0, 8, 0)
        root.addWidget(hint)

        root.addStretch()

        footer = QLabel('© theastravision.com')
        footer.setObjectName("subtitle")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

    def _start_browser_login(self):
        self.error_label.hide()
        self.status_label.setText("Opening browser — finish sign-in there, then return here.")
        self.status_label.show()
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Waiting for browser…")
        self.browser_login_requested.emit()

    def reset_login_button(self):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign in with HRMS")
        self.status_label.hide()

    def show_error(self, msg: str):
        self.reset_login_button()
        friendly = msg
        if "Employee profile" in msg or "403" in msg:
            friendly = "No employee profile linked. Run: python manage.py seed_wfh"
        elif "timed out" in msg.lower():
            friendly = "Login timed out. Try again and complete sign-in in the browser."
        elif "refused" in msg.lower() or "Connection" in msg:
            friendly = "Cannot reach API. Start: python manage.py runserver 127.0.0.1:8000"
        self.error_label.setText(friendly)
        self.error_label.show()
