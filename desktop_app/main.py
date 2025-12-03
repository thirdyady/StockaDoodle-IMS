"""
StockaDoodle Inventory Management System - Main Application Entry Point

This module initializes and runs the StockaDoodle IMS desktop application.
Handles application setup, window management, and the main event loop.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from utils.config import AppConfig
from ui.login_window import LoginWindow


def main():
    """
    Main application entry point.
    """
    # Create QApplication with StockaDoodle branding
    app = QApplication(sys.argv)
    app.setApplicationName("StockaDoodle")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StockaDoodle Inc.")

    # Set window icon
    icon_path = "../desktop_app/assets/icons/stockadoodle-transparent.png"
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Note: High DPI scaling is enabled by default in PyQt6

    # Create and show login window
    login_window = LoginWindow()

    # Handle successful login
    def on_login_successful(user_data):
        """Handle successful login by transitioning to main application."""
        print(f"Login successful for user: {user_data.get('username')}")
        # TODO: Create and show main window here
        # main_window = MainWindow(user_data)
        # main_window.show()
        # login_window.hide()

        # For now, just close the login window
        login_window.close()

    login_window.login_successful.connect(on_login_successful)
    login_window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()