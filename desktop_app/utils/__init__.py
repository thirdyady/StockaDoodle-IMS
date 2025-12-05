"""
Thin utils package initializer.

We intentionally keep this file minimal to avoid circular imports between
utils.config, utils.helpers, and other submodules.

In the desktop app, always import directly from submodules, e.g.:

    from utils.config import AppConfig
    from utils.helpers import format_currency, get_feather_icon
    from utils.theme import load_light_theme
"""

# Re-export AppConfig for convenience if someone does: from utils import AppConfig
from utils.config import AppConfig

__all__ = [
    "AppConfig",
]
