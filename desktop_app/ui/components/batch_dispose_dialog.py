from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt
from typing import Dict

from desktop_app.utils.api_wrapper import remove_stock_from_batch


class BatchDisposeDialog(QDialog):
    """Dialog for disposing stock from a specific batch."""

    def __init__(self, product_id: int, batch: Dict, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.batch = batch or {}
        self.batch_id = self.batch.get("id")
        self.max_quantity = int(self.batch.get("quantity", 0) or 0)

        self.setWindowTitle("Dispose Stock from Batch")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Dispose Stock from Batch #{self.batch_id}")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0A2A83;")
        layout.addWidget(title)

        info_label = QLabel(f"Available Quantity: {self.max_quantity} units")
        info_label.setStyleSheet("font-size: 13px; color: #64748b;")
        layout.addWidget(info_label)

        if self.max_quantity == 0:
            warning_label = QLabel("⚠️ This batch is empty and cannot be disposed from.")
            warning_label.setStyleSheet("font-size: 13px; color: #EF4444; font-weight: 600;")
            layout.addWidget(warning_label)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, max(1, self.max_quantity))
        self.quantity_input.setValue(1)
        self.quantity_input.setEnabled(self.max_quantity > 0)
        self.quantity_input.setMinimumWidth(200)
        form.addRow("Quantity to Dispose:", self.quantity_input)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g., Damaged, Expired, Lost, etc.")
        self.reason_input.setMinimumWidth(200)
        self.reason_input.setEnabled(self.max_quantity > 0)
        form.addRow("Reason:", self.reason_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)

        btn_dispose = QPushButton("Dispose")
        btn_dispose.setObjectName("primaryBtn")
        btn_dispose.setFixedHeight(36)
        btn_dispose.setEnabled(self.max_quantity > 0)
        btn_dispose.clicked.connect(self._on_dispose)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_dispose)
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
            QSpinBox, QLineEdit {
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                padding: 8px 12px;
                font-size: 13px;
                background: #FFFFFF;
            }
            QSpinBox:disabled, QLineEdit:disabled {
                background: #F3F6FF;
                color: #94A3B8;
            }
            QSpinBox:focus, QLineEdit:focus {
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
            QPushButton#primaryBtn:disabled {
                background: #CBD5E1;
                color: #94A3B8;
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

    def _on_dispose(self):
        if not self.batch_id:
            QMessageBox.warning(self, "Error", "Invalid batch ID.")
            return

        quantity = self.quantity_input.value()
        reason = self.reason_input.text().strip() or "Stock disposed"

        if quantity <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
            return

        if quantity > self.max_quantity:
            QMessageBox.warning(self, "Validation Error", f"Cannot dispose more than {self.max_quantity} units.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Disposal",
            f"Are you sure you want to dispose {quantity} units from this batch?\n\nReason: {reason}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            result = remove_stock_from_batch(
                product_id=self.product_id,
                batch_id=self.batch_id,
                quantity=quantity,
                reason=reason
            )

            if isinstance(result, dict):
                batch_info = result.get("batch") or {}
                new_qty = batch_info.get("quantity")
                if new_qty is None:
                    # Fallback if backend returns a different shape
                    new_qty = max(self.max_quantity - quantity, 0)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Stock disposed successfully!\n\nRemaining in batch: {new_qty} units"
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to dispose stock. Please try again.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to dispose stock:\n{str(e)}")
