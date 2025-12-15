from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDateEdit, QLineEdit, QMessageBox, QFormLayout
)
from PyQt6.QtCore import QDate, Qt

from desktop_app.utils.api_wrapper import add_stock_batch, get_current_user_data


class AddBatchDialog(QDialog):
    """Dialog for adding a new stock batch to a product."""

    def __init__(self, product_id: int, parent=None):
        super().__init__(parent)
        self.product_id = product_id

        self.setWindowTitle("Add New Stock Batch")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Add New Stock Batch")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0A2A83;")
        layout.addWidget(title)

        # Form fields
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 999_999)
        self.quantity_input.setValue(1)
        self.quantity_input.setMinimumWidth(200)
        form.addRow("Quantity:", self.quantity_input)

        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate().addDays(30))
        self.expiry_input.setMinimumWidth(200)
        form.addRow("Expiration Date:", self.expiry_input)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g., Restock, Return, etc.")
        self.reason_input.setMinimumWidth(200)
        form.addRow("Reason:", self.reason_input)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)

        btn_add = QPushButton("Add Batch")
        btn_add.setObjectName("primaryBtn")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._on_add)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_add)
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
            QSpinBox, QDateEdit, QLineEdit {
                border-radius: 8px;
                border: 1px solid #D3D8E5;
                padding: 8px 12px;
                font-size: 13px;
                background: #FFFFFF;
            }
            QSpinBox:focus, QDateEdit:focus, QLineEdit:focus {
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

    def _on_add(self):
        quantity = self.quantity_input.value()
        expiry_date = self.expiry_input.date().toPyDate()
        reason = self.reason_input.text().strip() or "Stock added"

        if quantity <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
            return

        try:
            user_data = get_current_user_data() or {}
            added_by = user_data.get("id")

            result = add_stock_batch(
                self.product_id,
                quantity=quantity,
                expiration_date=expiry_date.isoformat(),
                reason=reason,
                added_by=added_by
            )

            if isinstance(result, dict):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Stock batch added successfully!\nNew stock level: {result.get('new_stock_level', 'N/A')}"
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to add batch. Please try again.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add stock batch:\n{str(e)}")
