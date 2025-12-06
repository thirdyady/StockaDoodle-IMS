# desktop_app/utils/__init__.py
"""
Centralized exports for convenience.
Avoid circular imports by importing only leaf-level items here.

In the desktop app, always prefer importing from submodules directly, e.g.:

    from desktop_app.utils.config import AppConfig
    from desktop_app.utils.helpers import format_date, get_feather_icon
"""

from desktop_app.utils.config import AppConfig
from desktop_app.utils.app_state import AppState

__all__ = [
    "AppConfig",
    "AppState",
]
