"""
StockaDoodle Inventory Management System - Login Window

Features:
- Clean, modern UI with StockaDoodle branding
- API-based authentication via StockaDoodleAPI client
- MFA flow for Admin/Manager roles
- Responsive design with proper error handling
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

from api_client.stockadoodle_api import StockaDoodleAPI
from utils.helpers import get_feather_icon
from utils.styles import get_dialog_style
from utils.config import AppConfig


class LoginWindow(QWidget):
    """
    Login window for StockaDoodle IMS with API authentication and MFA support.
    """

    login_successful = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StockaDoodle - Inventory Management System")
        self.setFixedSize(400, 600)
        self.setStyleSheet(get_dialog_style())

        # Set window icon
        icon_path = "../desktop_app/assets/icons/stockadoodle-transparent.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Initialize API client
        self.api_client = StockaDoodleAPI()
        self.attempted_user = None

        self.init_ui()

    def init_ui(self):
        """Initialize the login window UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_path = "../desktop_app/assets/icons/stockadoodle-transparent.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("StockaDoodle")
            logo_label.setStyleSheet("font-size: 32pt; font-weight: bold; color: #2563EB;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo_label)

        # Title
        title = QLabel("Welcome Back!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 24pt; font-weight: bold; color: {AppConfig.LIGHT_TEXT};")
        main_layout.addWidget(title)

        subtitle = QLabel("Sign in to your StockaDoodle account")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {AppConfig.TEXT_COLOR_ALT}; font-size: 12pt;")
        main_layout.addWidget(subtitle)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, 
                                               QSizePolicy.Policy.Fixed))

        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(45)
        main_layout.addWidget(self.username_input)

        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(45)
        main_layout.addWidget(self.password_input)

        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setIcon(get_feather_icon("log-in", size=18))
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        main_layout.addWidget(self.login_btn)

        # Footer
        footer = QLabel("© 2025 StockaDoodle Inventory System")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: rgba(255,255,255,0.4); font-size: 10pt;")
        main_layout.addStretch()
        main_layout.addWidget(footer)

        # Allow Enter key to trigger login
        self.password_input.returnPressed.connect(self.login_btn.click)

    def handle_login(self):
        """Handle login button click - authenticate via API."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Required", 
                              "Please enter both username and password.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")

        try:
            # Attempt login via API
            result = self.api_client.login(username, password)

            # Check if MFA is required
            if result.get('mfa_required'):
                # MFA required - build user dict from individual fields
                self.attempted_user = {
                    'id': result.get('user_id'),
                    'username': result.get('username'),
                    'role': result.get('role'),
                    'email': result.get('email')
                }
                
                if not self.attempted_user.get('username'):
                    QMessageBox.critical(self, "Login Error", 
                                       "Invalid login response from server.")
                    self.reset_login_button()
                    return

                self.request_mfa()
            else:
                # Direct login successful (for staff/retailer)
                user = result.get('user')
                if user:
                    self.login_successful.emit(user)
                    self.close()
                else:
                    QMessageBox.critical(self, "Login Error", 
                                       "Invalid login response from server.")
                    self.reset_login_button()

        except Exception as e:
            error_msg = str(e)
            QMessageBox.critical(self, "Login Failed", 
                               f"Authentication failed:\n{error_msg}")
            self.reset_login_button()

    def request_mfa(self):
        """Initiate MFA flow for privileged users (Admin/Manager)."""
        email = self.attempted_user.get('email')
        if not email:
            QMessageBox.critical(self, "MFA Error", 
                               "No email configured for this account.")
            self.reset_login_button()
            return

        try:
            # Send MFA code via API
            result = self.api_client.send_mfa_code(
                self.attempted_user['username'],
                email
            )

            QMessageBox.information(
                self,
                "MFA Required",
                f"A 6-digit verification code has been sent to {email}"
            )

            # Show MFA dialog
            from ui.mfa_window import MFAWindow
            mfa_dialog = MFAWindow(self.attempted_user, parent=self)
            mfa_dialog.mfa_verified.connect(self.on_mfa_success)
            mfa_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "MFA Failed", 
                               f"Could not send MFA code:\n{str(e)}")
            self.reset_login_button()

    def on_mfa_success(self, verified_user):
        """Handle successful MFA verification."""
        self.login_successful.emit(verified_user)
        self.close()

    def reset_login_button(self):
        """Reset login button to default state."""
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign In")

    def mousePressEvent(self, event):
        """Allow dragging the window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Handle mouse release for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        if not hasattr(self, 'old_pos') or not self.old_pos:
            return
        delta = event.globalPosition().toPoint() - self.old_pos
        self.move(self.pos() + delta)
        self.old_pos = event.globalPosition().toPoint()