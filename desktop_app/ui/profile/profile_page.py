# desktop_app/ui/profile/profile_page.py

"""
Compatibility wrapper.

Older parts of the codebase may import:
    from desktop_app.ui.profile.profile_page import ProfilePage

The canonical ProfilePage now lives in:
    desktop_app.ui.pages.profile

This wrapper prevents import breakage while keeping a single source of truth.
"""

from __future__ import annotations

from desktop_app.ui.pages.profile import ProfilePage

__all__ = ["ProfilePage"]
