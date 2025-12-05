from datetime import datetime

def format_date(date_value, format_str: str = None) -> str:
    """
    Universal date formatter.
    Accepts string, datetime, or ISO timestamps.

    Examples:
        "2025-01-04"             → "Jan 04, 2025"
        "2025-01-04T13:22:00Z"   → "Jan 04, 2025"
        datetime(...)           → formatted date
    """

    # default format from config (if available)
    try:
        from utils.config import AppConfig
        default_format = AppConfig.DISPLAY_DATE_FORMAT
    except Exception:
        default_format = "%b %d, %Y"  # fallback

    if format_str is None:
        format_str = default_format

    # Handle datetime object
    if hasattr(date_value, "strftime"):
        return date_value.strftime(format_str)

    # Handle date string
    if isinstance(date_value, str):
        dt = None

        # Try ISO with Z
        try:
            dt = datetime.fromisoformat(date_value.replace("Z", "").replace("T", " "))
        except:
            pass

        # Try DB format (YYYY-MM-DD HH:MM:SS)
        if dt is None:
            try:
                dt = datetime.strptime(date_value.split()[0], "%Y-%m-%d")
            except:
                return date_value  # return unchanged

        return dt.strftime(format_str)

    return str(date_value)

# Temporary proxy for backward compatibility
# Delegates to icons module
try:
    from utils.icons import get_icon as get_feather_icon
except Exception:
    # As last fallback return dummy function
    def get_feather_icon(name: str, color: str = None, size: int = 24):
        print(f"[WARNING] get_feather_icon fallback used for '{name}'")
        from PyQt6.QtGui import QIcon
        return QIcon()
