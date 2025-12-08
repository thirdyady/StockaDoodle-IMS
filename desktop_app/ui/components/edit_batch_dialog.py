from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QLineEdit, QMessageBox, QFormLayout
)
from PyQt6.QtCore import QDate, Qt
from datetime import datetime
from typing import Dict

from desktop_app.utils.api_wrapper import update_batch_metadata


class EditBatchDialog(QDialog):
    """Dialog for editing batch metadata (expiration date and reason)."""

    def __init__(self, product_id: int, batch: Dict, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.batch = batch or {}
        self.batch_id = self.batch.get("id")

        self.setWindowTitle("Edit Stock Batch")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._build_ui()
        self._apply_styles()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Edit Batch #{self.batch_id}")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0A2A83;")
        layout.addWidget(title)

        qty_label = QLabel(f"Current Quantity: {self.batch.get('quantity', 0)} units")
        qty_label.setStyleSheet("font-size: 13px; color: #64748b;")
        layout.addWidget(qty_label)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setMinimumWidth(200)
        form.addRow("Expiration Date:", self.expiry_input)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g., Restock, Return, etc.")
        self.reason_input.setMinimumWidth(200)
        form.addRow("Reason:", self.reason_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Changes")
        btn_save.setObjectName("primaryBtn")
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
            }
            QLabel {
                font-size: 13px;
                color: #24324F;
            }
            QDateEdit, QLineEdit {
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                padding: 8px 12px;
                font-size: 13px;
                background: #FFFFFF;
            }
            QDateEdit:focus, QLineEdit:focus {
                border: 1px solid #7FA2FF;
                background: #F9FBFF;
            }
            QPushButton {
                padding: 8px 18px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton#primaryBtn {
                background: #0A2A83;
                color: white;
            }
            QPushButton#primaryBtn:hover {
                background: #153AAB;
            }
            QPushButton:not(#primaryBtn) {
                background: #F3F6FF;
                color: #0A2A83;
                border: 1px solid #D9E4FF;
            }
            QPushButton:not(#primaryBtn):hover {
                background: #E8EEFF;
            }
        """)

    def _populate(self):
        expiry_str = self.batch.get("expiration_date")

        if expiry_str:
            try:
                if isinstance(expiry_str, str):
                    expiry_date = datetime.fromisoformat(expiry_str.replace("Z", "")).date()
                else:
                    expiry_date = expiry_str

                qdate = QDate.fromString(expiry_date.isoformat(), "yyyy-MM-dd")
                if qdate.isValid():
                    self.expiry_input.setDate(qdate)
                else:
                    self.expiry_input.setDate(QDate.currentDate().addDays(30))
            except Exception:
                self.expiry_input.setDate(QDate.currentDate().addDays(30))
        else:
            self.expiry_input.setDate(QDate.currentDate().addDays(30))

        self.reason_input.setText(self.batch.get("reason", "") or "")

    def _on_save(self):
        if not self.batch_id:
            QMessageBox.warning(self, "Error", "Invalid batch ID.")
            return

        expiry_date = self.expiry_input.date().toPyDate()
        reason = self.reason_input.text().strip() or ""

        try:
            result = update_batch_metadata(
                product_id=self.product_id,
                batch_id=self.batch_id,
                expiration_date=expiry_date.isoformat(),
                reason=reason
            )

            if isinstance(result, dict):
                QMessageBox.information(self, "Success", "Batch metadata updated successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to update batch. Please try again.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update batch:\n{str(e)}")
