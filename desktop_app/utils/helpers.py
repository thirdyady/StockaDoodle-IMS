# desktop_app/utils/helpers.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

try:
    from desktop_app.utils.config import AppConfig
    _DEFAULT_DATE_FMT = getattr(AppConfig, "DISPLAY_DATE_FORMAT", "%b %d, %Y")
except Exception:
    _DEFAULT_DATE_FMT = "%b %d, %Y"


def format_date(date_value: Any, format_str: Optional[str] = None) -> str:
    """
    Formats datetime-like objects or ISO-ish strings into a display string.

    Safe behavior:
    - If parsing fails, returns original string.
    - If strftime fails, returns stringified input.
    """
    if format_str is None:
        format_str = _DEFAULT_DATE_FMT

    if hasattr(date_value, "strftime"):
        try:
            return date_value.strftime(format_str)
        except Exception:
            return str(date_value)

    if isinstance(date_value, str):
        dt = None

        # Try ISO-like parsing
        try:
            cleaned = date_value.replace("Z", "").replace("T", " ")
            dt = datetime.fromisoformat(cleaned)
        except Exception:
            dt = None

        # Try YYYY-MM-DD simple parse
        if dt is None:
            try:
                dt = datetime.strptime(date_value.split()[0], "%Y-%m-%d")
            except Exception:
                return date_value

        try:
            return dt.strftime(format_str)
        except Exception:
            return date_value

    return str(date_value)


# =========================================================
# Icon wrapper (safe + fallback + uniform tint support)
# =========================================================

try:
    from desktop_app.utils.icons import get_icon as _get_icon
except Exception:
    _get_icon = None


def _tint_qicon(icon, size: int, color: str):
    """
    Tint a QIcon by rendering to pixmap then applying SourceIn overlay.
    Safe utility for fallback Qt standard icons.
    """
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
    from PyQt6.QtCore import Qt

    try:
        pix = icon.pixmap(size, size)
        if pix.isNull():
            return icon

        tinted = QPixmap(pix.size())
        tinted.fill(Qt.GlobalColor.transparent)

        painter = QPainter(tinted)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        painter.drawPixmap(0, 0, pix)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color))
        painter.end()

        return QIcon(tinted)
    except Exception:
        return icon


def get_feather_icon(name: str, size: int = 24, color: Optional[str] = None):
    """
    Safe icon getter.

    Order:
    1) desktop_app.utils.icons.get_icon (if available)
    2) Qt standard icon fallback for known names
    3) Empty QIcon

    Supports uniform tint via `color`.
    """
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication, QStyle

    # Clamp size
    try:
        size = int(size)
    except Exception:
        size = 24
    if size <= 0:
        size = 16

    # 1) Try project icon loader
    if callable(_get_icon):
        try:
            icon = _get_icon(name, size=size, color=color)
            if isinstance(icon, QIcon) and not icon.isNull():
                return icon
        except Exception:
            pass

    # 2) Standard Qt fallback map
    fallback_map = {
        "home": QStyle.StandardPixmap.SP_ComputerIcon,
        "archive": QStyle.StandardPixmap.SP_DirIcon,
        "shopping-cart": QStyle.StandardPixmap.SP_DriveHDIcon,
        "bar-chart-2": QStyle.StandardPixmap.SP_FileDialogDetailedView,
        "settings": QStyle.StandardPixmap.SP_FileDialogContentsView,
        "activity": QStyle.StandardPixmap.SP_BrowserReload,
        "user": QStyle.StandardPixmap.SP_DirHomeIcon,
        "alert-triangle": QStyle.StandardPixmap.SP_MessageBoxWarning,
        "log-out": QStyle.StandardPixmap.SP_DialogCloseButton,
        "menu": QStyle.StandardPixmap.SP_TitleBarMenuButton,
        "chevron-up": QStyle.StandardPixmap.SP_ArrowUp,
        "chevron-down": QStyle.StandardPixmap.SP_ArrowDown,
        "chevron-left": QStyle.StandardPixmap.SP_ArrowLeft,
        "chevron-right": QStyle.StandardPixmap.SP_ArrowRight,
        "refresh-cw": QStyle.StandardPixmap.SP_BrowserReload,
        "search": QStyle.StandardPixmap.SP_FileDialogContentsView,
    }

    try:
        app = QApplication.instance()
        if app:
            pix = fallback_map.get((name or "").lower())
            if pix:
                std_icon = app.style().standardIcon(pix)
                if isinstance(std_icon, QIcon) and not std_icon.isNull():
                    if color:
                        return _tint_qicon(std_icon, size, color)
                    return std_icon
    except Exception:
        pass

    # 3) Last resort
    return QIcon()
