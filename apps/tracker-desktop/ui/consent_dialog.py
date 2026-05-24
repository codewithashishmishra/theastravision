from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import apply_window_icon, brand_logo_label

CONSENT_POINTS = [
    "Tracking is visible and consent-based during approved WFH only.",
    "The tracker opens fullscreen with a live activity table on screen.",
    "Tracking starts only when you click Start Work (task title and description required).",
    "Auto-pause after 1 minute with no keyboard or mouse activity.",
    "Activity pattern checks may flag possible spoofing (repeated keys, scroll-only, synthetic mouse) — no typed content is recorded.",
    "Screenshots are encrypted per company policy.",
    "Stopping work or closing the app syncs a full-day report to the server before exit.",
    "You may pause, resume, or stop tracking per your organization rules.",
]


class ConsentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WFH Tracking Consent")
        self.setFixedSize(460, 560)
        self.setModal(True)
        apply_window_icon(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        card = QFrame()
        card.setObjectName("card")
        card_inner = QVBoxLayout(card)
        card_inner.setContentsMargins(24, 24, 24, 20)
        card_inner.setSpacing(12)

        card_inner.addWidget(brand_logo_label(180, 64), alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("Consent required")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_inner.addWidget(title)

        intro = QLabel(
            "Before using the WFH tracker, please confirm you understand how monitoring works:"
        )
        intro.setObjectName("subtitle")
        intro.setWordWrap(True)
        intro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_inner.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        bullets_layout = QVBoxLayout(scroll_content)
        bullets_layout.setContentsMargins(4, 4, 4, 4)
        bullets_layout.setSpacing(4)
        for point in CONSENT_POINTS:
            row = QLabel(f"  •  {point}")
            row.setObjectName("bullet")
            row.setWordWrap(True)
            bullets_layout.addWidget(row)
        scroll.setWidget(scroll_content)
        card_inner.addWidget(scroll)

        root.addWidget(card, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        decline = QPushButton("Decline")
        decline.setObjectName("danger")
        decline.setMinimumHeight(44)
        decline.clicked.connect(self.reject)
        accept = QPushButton("I agree — continue")
        accept.setObjectName("primary")
        accept.setMinimumHeight(44)
        accept.clicked.connect(self.accept)
        btn_row.addWidget(decline, stretch=1)
        btn_row.addWidget(accept, stretch=2)
        root.addLayout(btn_row)
