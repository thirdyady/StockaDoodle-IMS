# desktop_app/ui/login_window.py
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

from api_client.stockadoodle_api import StockaDoodleAPI
from utils.helpers import get_feather_icon
from utils.config import AppConfig
from utils.styles import get_dialog_style

class LoginWindow(QWidget):
    login_successful = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StockaDoodle - Inventory Management System")
        self.setFixedSize(420, 640)
        self.setObjectName("loginWindow")

        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "stockadoodle-transparent.png")
        if os.path.exists(icon_path):
            try:
                self.setWindowIcon(QIcon(icon_path))
            except Exception:
                pass

        self.api_client = StockaDoodleAPI()
        self.attempted_user = None

        # small dialog stylesheet for login window
        self.setStyleSheet(get_dialog_style())

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 28, 36, 28)
        main_layout.setSpacing(18)

        logo_wrap = QHBoxLayout()
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "stockadoodle-transparent.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("StockaDoodle")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_wrap.addStretch()
        logo_wrap.addWidget(logo_label)
        logo_wrap.addStretch()
        main_layout.addLayout(logo_wrap)

        title = QLabel("Welcome Back!")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Sign in to your StockaDoodle account")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        main_layout.addSpacerItem(QSpacerItem(20, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.username_input = QLineEdit()
        self.username_input.setObjectName("loginInput")
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(44)
        main_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("loginInput")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(44)
        main_layout.addWidget(self.password_input)

        forgot_row = QHBoxLayout()
        forgot_row.addStretch()
        forgot_lbl = QLabel("")
        forgot_lbl.setObjectName("loginSmall")
        forgot_row.addWidget(forgot_lbl)
        main_layout.addLayout(forgot_row)

        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setIcon(get_feather_icon("log-in", size=16))
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        main_layout.addWidget(self.login_btn)

        main_layout.addStretch()

        footer = QLabel("© 2025 StockaDoodle Inventory System")
        footer.setObjectName("loginFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

        self.password_input.returnPressed.connect(self.login_btn.click)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Required", "Please enter both username and password.")
            return

        self._set_busy(True)
        try:
            result = self.api_client.login(username, password)
            if result.get("mfa_required"):
                self.attempted_user = {
                    "id": result.get("user_id"),
                    "username": result.get("username"),
                    "role": result.get("role"),
                    "email": result.get("email"),
                    "full_name": result.get("full_name", "")
                }
                self.request_mfa()
            else:
                user = result.get("user")
                if user:
                    self.login_successful.emit(user)
                    self.close()
                else:
                    QMessageBox.critical(self, "Login Error", "Invalid login response from server.")
                    self._set_busy(False)
        except Exception as e:
            QMessageBox.critical(self, "Login Failed", f"Authentication failed:\n{str(e)}")
            self._set_busy(False)

    def request_mfa(self):
        email = self.attempted_user.get("email")
        if not email:
            QMessageBox.critical(self, "MFA Error", "No email configured for this account.")
            self._set_busy(False)
            return
        try:
            self.api_client.send_mfa_code(self.attempted_user["username"], email)
            QMessageBox.information(self, "MFA Required", f"A verification code has been sent to {email}")
            from ui.mfa_window import MFAWindow
            mfa_dialog = MFAWindow(self.attempted_user, parent=self)
            mfa_dialog.mfa_verified.connect(self.on_mfa_success)
            mfa_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "MFA Failed", f"Could not send MFA code:\n{str(e)}")
            self._set_busy(False)

    def on_mfa_success(self, verified_user):
        self.login_successful.emit(verified_user)
        self.close()

    def _set_busy(self, busy: bool):
        if busy:
            self.login_btn.setEnabled(False)
            self.login_btn.setText("Signing in...")
        else:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")
