"""Shared UI widgets — logo and window icon."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from ui.theme import ICON_PATH


def load_brand_pixmap(max_width: int = 200, max_height: int = 88) -> QPixmap | None:
    if not ICON_PATH.exists():
        return None
    source = QPixmap(str(ICON_PATH))
    if source.isNull():
        return None
    return source.scaled(
        max_width,
        max_height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def brand_logo_label(max_width: int = 200, max_height: int = 88) -> QLabel:
    """Logo label sized to image aspect ratio (avoids clipping wide icons)."""
    label = QLabel()
    label.setObjectName("logo")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("background: transparent; border: none;")
    pixmap = load_brand_pixmap(max_width, max_height)
    if pixmap and not pixmap.isNull():
        label.setPixmap(pixmap)
        label.setFixedSize(pixmap.size())
    return label


def build_app_icon() -> QIcon:
    icon = QIcon()
    if not ICON_PATH.exists():
        return icon
    source = QPixmap(str(ICON_PATH))
    if source.isNull():
        return icon
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(
            source.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
    return icon


def apply_window_icon(widget: QWidget) -> None:
    icon = build_app_icon()
    if not icon.isNull():
        widget.setWindowIcon(icon)
