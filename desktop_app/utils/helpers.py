# desktop_app/utils/helpers.py

from datetime import datetime

try:
    from desktop_app.utils.config import AppConfig
    _DEFAULT_DATE_FMT = getattr(AppConfig, "DISPLAY_DATE_FORMAT", "%b %d, %Y")
except Exception:
    _DEFAULT_DATE_FMT = "%b %d, %Y"


def format_date(date_value, format_str: str | None = None) -> str:
    if format_str is None:
        format_str = _DEFAULT_DATE_FMT

    if hasattr(date_value, "strftime"):
        try:
            return date_value.strftime(format_str)
        except Exception:
            return str(date_value)

    if isinstance(date_value, str):
        dt = None
        try:
            cleaned = date_value.replace("Z", "").replace("T", " ")
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(cleaned)
        except Exception:
            dt = None

        if dt is None:
            try:
                from datetime import datetime as _dt
                dt = _dt.strptime(date_value.split()[0], "%Y-%m-%d")
            except Exception:
                return date_value

        try:
            return dt.strftime(format_str)
        except Exception:
            return date_value

    return str(date_value)


# icon wrapper
try:
    from desktop_app.utils.icons import get_icon as _get_icon

    from PyQt6.QtGui import QIcon

    def get_feather_icon(name: str, size: int = 24, color: str | None = None) -> QIcon:
        try:
            return _get_icon(name, size=size, color=color)
        except Exception:
            return QIcon()
except Exception:
    from PyQt6.QtGui import QIcon

    def get_feather_icon(name: str, size: int = 24, color: str | None = None) -> QIcon:
        return QIcon()
