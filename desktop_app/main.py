# desktop_app/main.py
import sys, os
sys.path.append(os.path.dirname(__file__))  # allow direct local imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # allow higher-level imports



from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from utils.config import AppConfig

# robust imports (desktop_app or module import location)
try:
    from ui.login_window import LoginWindow
    from ui.main_window import MainWindow
except Exception:
    from desktop_app.ui.login_window import LoginWindow
    from desktop_app.ui.main_window import MainWindow

# load theme
from utils.theme import load_light_theme

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StockaDoodle")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StockaDoodle Inc.")

    # apply theme (light default)
    app.setStyleSheet(load_light_theme())

    # set icon if exists
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "stockadoodle-transparent.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # create login window
    login_window = LoginWindow()

    def on_login_successful(user_data):
        print(f"Login successful for user: {user_data.get('username')}")
        main_window = MainWindow(user_data)
        main_window.show()
        # keep reference on login_window so GC doesn't close
        login_window.main_window = main_window
        login_window.hide()

    login_window.login_successful.connect(on_login_successful)
    login_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
