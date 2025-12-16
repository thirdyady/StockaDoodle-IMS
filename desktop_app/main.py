# desktop_app/main.py

import sys
import os
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from desktop_app.ui.login_window import LoginWindow
from desktop_app.ui.main_window import MainWindow

from desktop_app.utils.app_state import set_current_user
from desktop_app.utils.style_presets import get_global_stylesheet


def show_crash_dialog(exc_type, exc_value, exc_traceback):
    msg = QMessageBox()
    msg.setWindowTitle("🚨 Application Crash")
    msg.setIcon(QMessageBox.Icon.Critical)

    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("\n\n---------------- APPLICATION CRASHED ----------------")
    print(tb)

    msg.setText("The application crashed due to an error.")
    msg.setDetailedText(tb)
    msg.exec()


# Catch exceptions anywhere in the Qt loop
sys.excepthook = show_crash_dialog


class AppController:
    """
    Controls window switching:
    LoginWindow -> MainWindow -> Logout -> LoginWindow
    """

    def __init__(self):
        self.login_window: LoginWindow | None = None
        self.main_window: MainWindow | None = None

    def show_login(self):
        # close main if exists
        if self.main_window is not None:
            try:
                self.main_window.close()
            except Exception:
                pass
            self.main_window = None

        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.show()

    def on_login_successful(self, user_data: dict):
        print(">>> LOGIN SUCCESSFUL:", user_data)
        set_current_user(user_data)

        # close login
        if self.login_window is not None:
            try:
                self.login_window.close()
            except Exception:
                pass
            self.login_window = None

        # open main
        self.main_window = MainWindow(user_data)

        # ✅ when main emits logout, go back to login
        self.main_window.logout_requested.connect(self.on_logout_requested)

        self.main_window.show()

    def on_logout_requested(self):
        # Clear global user if you want
        try:
            set_current_user({})
        except Exception:
            pass

        # Show login again
        self.show_login()


def main():
    app = QApplication(sys.argv)

    # ✅ IMPORTANT: don't quit when switching windows
    app.setQuitOnLastWindowClosed(False)

    # ✅ Apply ONE global stylesheet once
    try:
        app.setStyleSheet(get_global_stylesheet())
    except Exception as e:
        print("[WARNING] Failed to apply global stylesheet:", e)

    # Global icon
    icon_path = os.path.join(
        os.path.dirname(__file__), "assets", "icons", "stockadoodle-transparent.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print("[WARNING] App icon missing at:", icon_path)

    controller = AppController()
    controller.show_login()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
