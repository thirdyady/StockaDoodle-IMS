# desktop_app/ui/mfa_window.py
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from desktop_app.api_client.stockadoodle_api import StockaDoodleAPI
from desktop_app.utils.helpers import get_feather_icon
from desktop_app.utils.styles import get_dialog_style


class MFAWindow(QDialog):
    mfa_verified = pyqtSignal(dict)

    def __init__(self, user_data: dict, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.api_client = StockaDoodleAPI()
        self._verifying = False

        self.setWindowTitle("Two-Factor Authentication")
        self.setFixedSize(380, 300)
        self.setStyleSheet(get_dialog_style())
        self.setModal(True)

        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "icons", "stockadoodle-transparent.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Two-Factor Authentication")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "A verification code has been sent to your email.\n"
            "Please enter the 6-digit code below."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 6-digit code")
        self.code_input.setMaxLength(6)
        self.code_input.setFont(QFont("Consolas", 18))
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setFixedHeight(60)
        self.code_input.textChanged.connect(self.format_code_input)
        self.code_input.textChanged.connect(self.check_auto_submit)
        layout.addWidget(self.code_input)

        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setIcon(get_feather_icon("x"))
        cancel_btn.clicked.connect(self.reject)

        verify_btn = QPushButton("Verify")
        verify_btn.setIcon(get_feather_icon("check-circle"))
        verify_btn.clicked.connect(self.verify_code)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(verify_btn)
        layout.addLayout(btn_layout)

    def format_code_input(self, text):
        if not text.isdigit():
            self.code_input.setText("".join(filter(str.isdigit, text)))

    def check_auto_submit(self):
        if len(self.code_input.text()) == 6 and not self._verifying:
            self.verify_code()

    def verify_code(self):
        if self._verifying:
            return

        code = self.code_input.text().strip()

        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "Invalid Code", "Please enter a valid 6-digit code.")
            return

        self._verifying = True

        try:
            result = self.api_client.verify_mfa_code(self.user_data["username"], code)
            user = result.get("user")

            if user:
                QMessageBox.information(self, "Success", "Authentication successful!")
                self.mfa_verified.emit(user)
                self.accept()
            else:
                QMessageBox.critical(self, "Verification Failed", "Invalid verification code.")
                self.code_input.clear()
                self.code_input.setFocus()

        except Exception as e:
            QMessageBox.critical(self, "Verification Failed", f"Code verification failed:\n{e}")
            self.code_input.clear()
            self.code_input.setFocus()
        finally:
            self._verifying = False
