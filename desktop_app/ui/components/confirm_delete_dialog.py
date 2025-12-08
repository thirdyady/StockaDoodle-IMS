from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox
)
from typing import Dict, Callable, Optional


class ConfirmDeleteDialog(QDialog):
    """
    GitHub-style secure deletion dialog.
    Requires user to type the current stock level to confirm deletion.
    """
    
    def __init__(self, product: Dict, on_confirm: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self.product = product
        self.on_confirm = on_confirm
        self.product_id = product.get("id")
        self.product_name = product.get("name", "Unknown Product")
        self.current_stock = product.get("stock_level", 0)
        
        self.setWindowTitle("⚠️ Delete Product")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._build_ui()
        self._apply_styles()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Warning icon and title
        title = QLabel("⚠️ Delete Product")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #EF4444;")
        layout.addWidget(title)
        
        # Warning message
        warning_text = QLabel(f"Are you absolutely sure you want to delete:")
        warning_text.setStyleSheet("font-size: 14px; color: #24324F;")
        layout.addWidget(warning_text)
        
        # Product name (highlighted)
        product_label = QLabel(self.product_name)
        product_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #0A2A83;
            padding: 8px;
            background: #F3F6FF;
            border-radius: 6px;
        """)
        layout.addWidget(product_label)
        
        # Consequences
        consequences_label = QLabel("This will permanently remove:")
        consequences_label.setStyleSheet("font-size: 13px; color: #64748b; margin-top: 8px;")
        layout.addWidget(consequences_label)
        
        consequences_list = QLabel(
            f"• All stock batches ({self.current_stock} units total)\n"
            f"• Product history and logs\n"
            f"• Category association"
        )
        consequences_list.setStyleSheet("font-size: 13px; color: #475569; padding-left: 12px;")
        layout.addWidget(consequences_list)
        
        # Confirmation input
        confirm_label = QLabel(f"👉 To confirm, type the current stock level: <b>{self.current_stock}</b>")
        confirm_label.setStyleSheet("font-size: 13px; color: #24324F; margin-top: 16px;")
        confirm_label.setTextFormat(confirm_label.TextFormat.RichText)
        layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText(f"Type {self.current_stock} to confirm")
        self.confirm_input.setMinimumHeight(40)
        self.confirm_input.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.confirm_input)
        
        layout.addStretch()
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("deleteBtn")
        self.btn_delete.setFixedHeight(38)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_delete)
        layout.addLayout(btn_row)
    
    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
            }
            QLineEdit {
                border-radius: 8px;
                border: 2px solid #EF4444;
                padding: 10px 14px;
                font-size: 14px;
                background: #FFFFFF;
                font-weight: 600;
            }
            QLineEdit:focus {
                border: 2px solid #DC2626;
                background: #FEF2F2;
            }
            QPushButton {
                padding: 10px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton#deleteBtn {
                background: #EF4444;
                color: white;
            }
            QPushButton#deleteBtn:hover {
                background: #DC2626;
            }
            QPushButton#deleteBtn:disabled {
                background: #CBD5E1;
                color: #94A3B8;
            }
            QPushButton:not(#deleteBtn) {
                background: #F3F6FF;
                color: #0A2A83;
                border: 1px solid #D9E4FF;
            }
            QPushButton:not(#deleteBtn):hover {
                background: #E8EEFF;
            }
        """)
    
    def _on_input_changed(self, text: str):
        """Enable delete button only if input matches current stock level."""
        try:
            input_value = int(text.strip())
            is_valid = (input_value == self.current_stock)
        except (ValueError, AttributeError):
            is_valid = False
        
        self.btn_delete.setEnabled(is_valid)
        
        # Visual feedback
        if text.strip() and not is_valid:
            self.confirm_input.setStyleSheet("""
                QLineEdit {
                    border-radius: 8px;
                    border: 2px solid #F59E0B;
                    padding: 10px 14px;
                    font-size: 14px;
                    background: #FFFBEB;
                    font-weight: 600;
                }
            """)
        else:
            self.confirm_input.setStyleSheet("""
                QLineEdit {
                    border-radius: 8px;
                    border: 2px solid #EF4444;
                    padding: 10px 14px;
                    font-size: 14px;
                    background: #FFFFFF;
                    font-weight: 600;
                }
                QLineEdit:focus {
                    border: 2px solid #10B981;
                    background: #F0FDF4;
                }
            """)
    
    def _on_delete(self):
        """Handle delete confirmation."""
        if not self.btn_delete.isEnabled():
            return
        
        # Final confirmation
        reply = QMessageBox.question(
            self,
            "Final Confirmation",
            f"<b>Are you absolutely certain?</b><br><br>"
            f"This will <b>permanently delete</b> '{self.product_name}' and all associated data.<br>"
            f"This action <b>cannot be undone</b>.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.on_confirm:
                try:
                    self.on_confirm(self.product_id)
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Product '{self.product_name}' has been deleted successfully."
                    )
                    self.accept()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to delete product:\n{str(e)}"
                    )
            else:
                self.accept()

