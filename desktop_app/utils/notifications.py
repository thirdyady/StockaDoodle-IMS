# notifications.py
#
# This module provides toast-style notification messages for the application.
# Displays temporary popup messages that auto-dismiss after a timeout period.
#
# Usage: Imported by UI modules to show success, error, warning, and info messages.

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QIcon, QPixmap
from utils.config import AppConfig
from utils.icons import get_icon


class ToastNotification(QWidget):
    """A toast-style notification widget that appears temporarily."""
    
    def __init__(self, message: str, notification_type: str = "info", parent=None):
        """
        Initialize a toast notification.
        
        Args:
            message: The message text to display
            notification_type: Type of notification ("success", "error", "warning", "info")
            parent: Parent widget
        """
        super().__init__(parent)
        self.notification_type = notification_type
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui(message)
        self.setup_animation()
        
    def init_ui(self, message: str):
        """Initialize the UI components."""
        # Color mapping
        colors = {
            "success": ("#00B894", "#2ED573"),
            "error": ("#D63031", "#FF6B6B"),
            "warning": ("#FDCB6E", "#FFA502"),
            "info": (AppConfig.PRIMARY_COLOR, AppConfig.INFO_COLOR)
        }
        
        bg_color, accent_color = colors.get(self.notification_type, colors["info"])
        
        # Icon mapping
        icons = {
            "success": "check-circle",
            "error": "x-circle",
            "warning": "alert-triangle",
            "info": "info"
        }
        
        icon_name = icons.get(self.notification_type, "info")
        
        # Main container
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
                max-width: 400px;
            }}
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel()
        icon = get_icon(icon_name, accent_color, 24)
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
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
    
    def setup_animation(self):
        """Setup fade-in and slide animations."""
        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out.finished.connect(self.close)
        
        # Start fade in
        self.fade_in.start()
    
    def show_and_dismiss(self, timeout: int = None):
        """
        Show the notification and auto-dismiss after timeout.
        
        Args:
            timeout: Dismiss timeout in milliseconds (defaults to AppConfig.NOTIFICATION_TIMEOUT)
        """
        if timeout is None:
            timeout = AppConfig.NOTIFICATION_TIMEOUT
        
        self.show()
        QTimer.singleShot(timeout, self.dismiss)
    
    def dismiss(self):
        """Dismiss the notification with fade-out animation."""
        self.fade_out.start()


_notification_widgets = []  # Track active notifications


def _get_parent_window():
    """Get the main application window as parent."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            if widget.isWindow() and not isinstance(widget, ToastNotification):
                return widget
    return None


def show_notification(message: str, notification_type: str = "info", timeout: int = None):
    """
    Show a toast notification.
    
    Args:
        message: The message to display
        notification_type: Type of notification ("success", "error", "warning", "info")
        timeout: Auto-dismiss timeout in milliseconds
    """
    parent = _get_parent_window()
    
    toast = ToastNotification(message, notification_type, parent)
    
    if parent:
        # Position relative to parent window
        parent_rect = parent.geometry()
        
        # Calculate position based on AppConfig.NOTIFICATION_POSITION
        position = AppConfig.NOTIFICATION_POSITION
        
        if "top-right" in position:
            x = parent_rect.right() - 420
            y = parent_rect.top() + 80 + (len(_notification_widgets) * 80)
        elif "top-left" in position:
            x = parent_rect.left() + 20
            y = parent_rect.top() + 80 + (len(_notification_widgets) * 80)
        elif "bottom-right" in position:
            x = parent_rect.right() - 420
            y = parent_rect.bottom() - 100 - (len(_notification_widgets) * 80)
        else:  # bottom-left
            x = parent_rect.left() + 20
            y = parent_rect.bottom() - 100 - (len(_notification_widgets) * 80)
        
        toast.move(x, y)
    
    toast.show_and_dismiss(timeout)
    _notification_widgets.append(toast)
    
    # Remove from list after dismissal
    def remove_from_list():
        if toast in _notification_widgets:
            _notification_widgets.remove(toast)
    
    toast.fade_out.finished.connect(remove_from_list)


def success(message: str, timeout: int = None):
    """Show a success notification."""
    show_notification(message, "success", timeout)


def error(message: str, timeout: int = None):
    """Show an error notification."""
    show_notification(message, "error", timeout)


def warning(message: str, timeout: int = None):
    """Show a warning notification."""
    show_notification(message, "warning", timeout)


def info(message: str, timeout: int = None):
    """Show an info notification."""
    show_notification(message, "info", timeout)

