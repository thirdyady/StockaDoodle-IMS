# desktop_app/utils/notifications.py
#
# Toast-style notification messages.

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from desktop_app.utils.config import AppConfig
from desktop_app.utils.icons import get_icon


class ToastNotification(QWidget):
    """A toast-style notification widget that appears temporarily."""

    def __init__(self, message: str, notification_type: str = "info", parent=None):
        super().__init__(parent)
        self.notification_type = notification_type

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._init_ui(message)
        self._setup_animation()

    def _init_ui(self, message: str):
        colors = {
            "success": ("#00B894", "#2ED573"),
            "error": ("#D63031", "#FF6B6B"),
            "warning": ("#FDCB6E", "#FFA502"),
            "info": (AppConfig.PRIMARY_COLOR, AppConfig.INFO_COLOR)
        }

        _, accent_color = colors.get(self.notification_type, colors["info"])

        icons = {
            "success": "check-circle",
            "error": "x-circle",
            "warning": "alert-triangle",
            "info": "info"
        }
        icon_name = icons.get(self.notification_type, "info")

        container = QWidget()
        container.setObjectName("toastContainer")
        container.setStyleSheet(f"""
            #toastContainer {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border: 2px solid {accent_color};
                border-left: 4px solid {accent_color};
                border-radius: {AppConfig.BUTTON_RADIUS}px;
                padding: 15px 20px;
                min-width: 300px;
                max-width: 420px;
            }}
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Icon (FIXED CALL)
        icon_label = QLabel()
        icon = get_icon(icon_name, size=24, color=accent_color)
        icon_label.setPixmap(icon.pixmap(24, 24))
        layout.addWidget(icon_label)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            color: {AppConfig.TEXT_COLOR};
            font-size: {AppConfig.FONT_SIZE_MEDIUM}pt;
            background-color: transparent;
        """)
        layout.addWidget(message_label, 1)

        # Close button
        close_btn = QLabel("×")
        close_btn.setStyleSheet(f"""
            color: {AppConfig.TEXT_COLOR_ALT};
            font-size: 20pt;
            font-weight: bold;
            background-color: transparent;
            padding: 0px;
        """)
        close_btn.mousePressEvent = lambda e: self.close()
        layout.addWidget(close_btn)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

    def _setup_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_in_anim.setDuration(250)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_out_anim.setDuration(250)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self.close)

        self.fade_in_anim.start()

    def show_and_dismiss(self, timeout: int | None = None):
        if timeout is None:
            timeout = AppConfig.NOTIFICATION_TIMEOUT

        self.show()
        QTimer.singleShot(timeout, self.dismiss)

    def dismiss(self):
        self.fade_out_anim.start()


_notification_widgets = []


def _get_parent_window():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            if widget.isWindow() and not isinstance(widget, ToastNotification):
                return widget
    return None


def show_notification(message: str, notification_type: str = "info", timeout: int | None = None):
    parent = _get_parent_window()
    toast = ToastNotification(message, notification_type, parent)

    if parent:
        parent_rect = parent.geometry()
        position = AppConfig.NOTIFICATION_POSITION

        stack_offset = len(_notification_widgets) * 80

        if "top-right" in position:
            x = parent_rect.right() - 440
            y = parent_rect.top() + 80 + stack_offset
        elif "top-left" in position:
            x = parent_rect.left() + 20
            y = parent_rect.top() + 80 + stack_offset
        elif "bottom-right" in position:
            x = parent_rect.right() - 440
            y = parent_rect.bottom() - 100 - stack_offset
        else:
            x = parent_rect.left() + 20
            y = parent_rect.bottom() - 100 - stack_offset

        toast.move(x, y)

    toast.show_and_dismiss(timeout)
    _notification_widgets.append(toast)

    def remove_from_list():
        if toast in _notification_widgets:
            _notification_widgets.remove(toast)

    toast.fade_out_anim.finished.connect(remove_from_list)


def success(message: str, timeout: int | None = None):
    show_notification(message, "success", timeout)


def error(message: str, timeout: int | None = None):
    show_notification(message, "error", timeout)


def warning(message: str, timeout: int | None = None):
    show_notification(message, "warning", timeout)


def info(message: str, timeout: int | None = None):
    show_notification(message, "info", timeout)
