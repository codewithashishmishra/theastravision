import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from core.api_client import ApiClient

class BugReportDialog(QDialog):
    def __init__(self, parent=None, client: ApiClient = None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Report a Bug")
        self.setMinimumSize(500, 400)
        
        self.selected_file_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Report a Bug or Issue")
        header.setObjectName("heading")
        layout.addWidget(header)

        desc_label = QLabel("Description:")
        desc_label.setObjectName("subtitle")
        layout.addWidget(desc_label)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Please describe what went wrong...")
        layout.addWidget(self.desc_input, stretch=1)

        self.file_label = QLabel("No screenshot attached.")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #64748b; font-size: 13px;")
        
        btn_attach = QPushButton("Attach Screenshot (Optional)")
        btn_attach.setObjectName("secondary")
        btn_attach.clicked.connect(self._select_file)

        file_row = QHBoxLayout()
        file_row.addWidget(btn_attach)
        file_row.addWidget(self.file_label, stretch=1)
        layout.addLayout(file_row)

        btns_row = QHBoxLayout()
        btns_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("secondary")
        btn_cancel.clicked.connect(self.reject)

        self.btn_submit = QPushButton("Submit Report")
        self.btn_submit.setObjectName("primary")
        self.btn_submit.clicked.connect(self._submit)

        btns_row.addWidget(btn_cancel)
        btns_row.addWidget(self.btn_submit)
        layout.addLayout(btns_row)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Screenshot", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.selected_file_path = path
            self.file_label.setText(f"Attached: {path.split('/')[-1]}")
            self.file_label.setStyleSheet("color: #10b981; font-weight: bold;")

    def _submit(self):
        desc = self.desc_input.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Validation Error", "Please enter a description.")
            return

        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("Submitting...")

        payload = {"description": desc}
        
        # Optional screenshot metadata; backend stores a short key (<=512 chars).
        if self.selected_file_path:
            try:
                filename = os.path.basename(self.selected_file_path)
                payload["screenshot_key"] = f"local://{filename}"[:512]
                payload["description"] = f"{desc}\n\n[attachment: {filename}]"
            except Exception:
                pass

        try:
            self.client.post("/bug-report/", json=payload)
            QMessageBox.information(self, "Success", "Bug report submitted successfully! Thank you.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to submit bug report: {e}")
            self.btn_submit.setEnabled(True)
            self.btn_submit.setText("Submit Report")
