from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ui.widgets import apply_window_icon, brand_logo_label


class StartWorkDialog(QDialog):
    """Collect today's task before starting visible tracking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Start work — today's task")
        self.setFixedSize(480, 420)
        self.setModal(True)
        apply_window_icon(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 20, 24, 20)
        inner.setSpacing(12)

        inner.addWidget(brand_logo_label(160, 56), alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("What are you working on today?")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title)

        intro = QLabel(
            "Enter a short title and description of your task. "
            "This is stored with your WFH session for HR/manager visibility."
        )
        intro.setObjectName("subtitle")
        intro.setWordWrap(True)
        intro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(intro)

        lbl_title = QLabel("Task title")
        lbl_title.setObjectName("subtitle")
        inner.addWidget(lbl_title)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. API integration for payroll module")
        self.title_input.setMinimumHeight(40)
        inner.addWidget(self.title_input)

        lbl_desc = QLabel("Task description")
        lbl_desc.setObjectName("subtitle")
        inner.addWidget(lbl_desc)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText(
            "Describe what you plan to accomplish today, milestones, or deliverables…"
        )
        self.desc_input.setMinimumHeight(100)
        inner.addWidget(self.desc_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.hide()
        inner.addWidget(self.error_label)

        root.addWidget(card, stretch=1)

        self.start_btn = QPushButton("Start tracking")
        self.start_btn.setObjectName("primary")
        self.start_btn.setMinimumHeight(46)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start)
        root.addWidget(self.start_btn)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("secondary")
        cancel.setMinimumHeight(40)
        cancel.clicked.connect(self.reject)
        root.addWidget(cancel)

        self.title_input.setFocus()

    def _on_start(self):
        title = self.title_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        if not title:
            self._show_error("Please enter a task title.")
            return
        if len(title) < 3:
            self._show_error("Task title must be at least 3 characters.")
            return
        if not desc:
            self._show_error("Please describe what you are doing today.")
            return
        if len(desc) < 10:
            self._show_error("Task description must be at least 10 characters.")
            return
        self.error_label.hide()
        self.accept()

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()

    def task_title(self) -> str:
        return self.title_input.text().strip()

    def task_description(self) -> str:
        return self.desc_input.toPlainText().strip()
