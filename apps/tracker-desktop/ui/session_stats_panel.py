from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.api_client import ApiClient

class SessionStatsPanel(QWidget):
    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Recent Activity (30 Days)")
        title.setObjectName("heading")
        layout.addWidget(title)

        self.summary_label = QLabel("Start a work session to see live stats.")
        self.summary_label.setObjectName("subtitle")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Task", "Start", "End", "Active", "Idle", "Paused", "Status", "Screenshots"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMouseTracking(True)
        self.table.viewport().setMouseTracking(True)
        card_layout.addWidget(self.table)
        layout.addWidget(card, stretch=1)
        
        self.refresh_history()

    def refresh_history(self):
        try:
            sessions = self.client.get("/sessions/history/")
            self.table.setRowCount(len(sessions))
            for i, sess in enumerate(sessions):
                start_full = sess.get("start_time", "")
                end_full = sess.get("end_time", "")
                
                date_str = start_full.split("T")[0] if "T" in start_full else ""
                
                # Convert UTC string to local time (simplified for display)
                # "2026-05-23T11:13:04.287593Z"
                start_time_str = start_full.split("T")[1][:5] if "T" in start_full else ""
                end_time_str = end_full.split("T")[1][:5] if end_full and "T" in end_full else "Active"
                
                task = sess.get("task_title", "")
                
                active_s = int(sess.get("active_duration") or 0)
                idle_s = int(sess.get("idle_duration") or 0)
                paused_s = int(sess.get("paused_duration") or 0)
                total_s = int(sess.get("total_duration") or 0)
                if active_s == 0 and idle_s == 0 and paused_s == 0 and total_s > 0:
                    active_s = total_s

                def fmt(s):
                    h = s // 3600
                    m = (s % 3600) // 60
                    return f"{h}h {m}m"

                row_data = [
                    date_str,
                    task,
                    start_time_str,
                    end_time_str,
                    fmt(active_s),
                    fmt(idle_s),
                    fmt(paused_s),
                    sess.get("status", "").capitalize(),
                    str(sess.get("screenshot_count", 0))
                ]
                
                for col, text in enumerate(row_data):
                    item = QTableWidgetItem(str(text))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(i, col, item)
        except Exception as e:
            import sys
            print(f"Error fetching history: {e}", file=sys.stderr)


    def update_from_stats(self, stats):
        if not stats or not stats.task_title:
            self.summary_label.setText("Start a work session to see live stats.")
            self.table.setRowCount(0)
            return
        self.summary_label.setText(
            f"<b>{stats.task_title}</b><br>"
            f"{stats.task_description[:200]}{'…' if len(stats.task_description) > 200 else ''}<br><br>"
            f"Active: {stats.format_hours(stats.active_sec)} · "
            f"Idle: {stats.format_hours(stats.idle_sec)} · "
            f"Paused: {stats.format_hours(stats.paused_sec)} · "
            f"Spoof flags: {len(stats.spoof_flags)}"
        )
        
        # When stats update, also refresh the history table so the current session shows live
        self.refresh_history()
