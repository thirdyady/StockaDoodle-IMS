import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from desktop_app.ui.login_window import LoginWindow
from desktop_app.ui.main_window import MainWindow

from desktop_app.utils.app_state import set_current_user


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

# IMPORTANT — holds main window so app doesn't close
_app_main_window_ref = None


def on_login_successful(user_data: dict):
    global _app_main_window_ref

    print(">>> LOGIN SUCCESSFUL:", user_data)
    set_current_user(user_data)

    try:
        main_window = MainWindow(user_data)

        # STORE IT HERE
        _app_main_window_ref = main_window

        main_window.show()

    except Exception as e:
        print("❌ ERROR WHILE OPENING MAIN WINDOW:", str(e))
        raise e


def main():
    app = QApplication(sys.argv)

    # Global icon
    icon_path = os.path.join(
        os.path.dirname(__file__), "assets", "icons", "stockadoodle-transparent.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print("[WARNING] App icon missing at:", icon_path)

    login_window = LoginWindow()
    login_window.login_successful.connect(on_login_successful)
    login_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
