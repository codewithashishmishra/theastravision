"""Aastraa brand theme — orange gradient, clean cards."""

from pathlib import Path

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
ICON_PATH = RESOURCES / "app_icon.png"

COLORS = {
    "primary": "#f97316",
    "primary_dark": "#ea580c",
    "primary_light": "#fdba74",
    "bg": "#0f172a",
    "bg_card": "#1e293b",
    "bg_input": "#334155",
    "text": "#f8fafc",
    "text_muted": "#94a3b8",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",
    "border": "#475569",
    "table_row": "#212121",
    "table_row_alt": "#1a1a1a",
}

APP_STYLESHEET = f"""
QWidget {{
    background-color: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}}
QLabel {{
    background: transparent;
    border: none;
}}
QLabel#title {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS["text"]};
    padding: 4px 0;
}}
QLabel#heading {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS["text"]};
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {COLORS["text_muted"]};
    line-height: 1.45;
    padding: 2px 0;
}}
QLabel#bullet {{
    font-size: 13px;
    color: {COLORS["text_muted"]};
    padding: 6px 0 6px 8px;
}}
QLabel#error {{
    color: {COLORS["danger"]};
    font-size: 12px;
    padding: 10px 12px;
    background-color: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 8px;
}}
QLabel#info {{
    color: {COLORS["text_muted"]};
    font-size: 12px;
    padding: 10px 12px;
    background-color: {COLORS["bg_input"]};
    border-radius: 8px;
}}
QFrame#card {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 16px;
}}
QPushButton#primary {{
    background-color: {COLORS["primary"]};
    color: white;
    border: none;
    border-radius: 10px;
    padding: 14px 20px;
    font-weight: 600;
    font-size: 14px;
    min-height: 20px;
}}
QPushButton#primary:hover {{
    background-color: {COLORS["primary_dark"]};
}}
QPushButton#primary:pressed {{
    background-color: #c2410c;
}}
QPushButton#primary:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_muted"]};
}}
QPushButton#secondary {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 12px 16px;
    font-weight: 500;
}}
QPushButton#secondary:hover {{
    border-color: {COLORS["primary"]};
}}
QPushButton#danger {{
    background-color: rgba(239, 68, 68, 0.12);
    color: #fca5a5;
    border: 1px solid {COLORS["danger"]};
    border-radius: 10px;
    padding: 12px 16px;
}}
QLabel#statusBanner {{
    border-radius: 12px;
    padding: 24px;
    font-size: 18px;
    font-weight: 700;
}}
QMainWindow {{
    background-color: {COLORS["bg"]};
}}
QDialog {{
    background-color: {COLORS["bg"]};
}}
QStatusBar {{
    background: {COLORS["bg_card"]};
    color: {COLORS["text_muted"]};
    border-top: 1px solid {COLORS["border"]};
    padding: 4px 8px;
    font-size: 12px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QLineEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {COLORS["primary"]};
}}
QTextEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
}}
QTextEdit:focus {{
    border-color: {COLORS["primary"]};
}}
QTableWidget, QTableView {{
    background-color: {COLORS["table_row"]};
    alternate-background-color: {COLORS["table_row_alt"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    gridline-color: {COLORS["border"]};
    selection-background-color: {COLORS["primary"]};
    selection-color: #ffffff;
    outline: none;
}}
QTableWidget::item, QTableView::item {{
    background-color: {COLORS["table_row"]};
    color: {COLORS["text"]};
    padding: 8px 6px;
    border: none;
}}
QTableWidget::item:alternate, QTableView::item:alternate {{
    background-color: {COLORS["table_row_alt"]};
}}
QTableWidget::item:hover, QTableView::item:hover {{
    background-color: {COLORS["primary"]};
    color: #ffffff;
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {COLORS["primary_dark"]};
    color: #ffffff;
}}
QTableWidget::item:selected:hover, QTableView::item:selected:hover {{
    background-color: {COLORS["primary"]};
    color: #ffffff;
}}
QHeaderView::section {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_muted"]};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {COLORS["border"]};
    font-weight: 600;
}}
QSplitter::handle {{
    background: {COLORS["border"]};
    width: 2px;
}}
"""
