"""
Compatibility theme module.

Your project has older files that may still import:
- load_light_theme()
- load_app_theme()

To prevent theme stacking and gray label strips,
we redirect ALL theme calls to the single source:
desktop_app.utils.app_theme.load_app_theme
"""

from desktop_app.utils.app_theme import load_app_theme as _load_app_theme


def load_app_theme() -> str:
    return _load_app_theme()


# Backward compatible alias for older code
def load_light_theme() -> str:
    return _load_app_theme()
