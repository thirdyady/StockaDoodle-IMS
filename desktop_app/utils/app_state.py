# app_state.py
#
# This module manages global application state that needs to be accessed
# across multiple UI components and modules.

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal


class AppState(QObject):
    """
    Singleton class for managing global application state.
    Uses Qt signals for state change notifications.
    """

    # Signals emitted when state changes
    user_changed = pyqtSignal(dict)      # Emitted when current_user changes
    theme_changed = pyqtSignal(bool)     # Emitted when theme changes (True = dark)
    product_selected = pyqtSignal(int)   # Emitted when a product is selected

    def __init__(self):
        super().__init__()
        self._current_user: Optional[Dict[str, Any]] = None
        self._api_client: Optional[Any] = None
        self._is_dark_mode: bool = True
        self._selected_product_id: Optional[int] = None
        self._selected_category_id: Optional[int] = None
        self._notifications: list = []

    # --------------------------------------------------------------------------
    # USER STATE MANAGEMENT
    # --------------------------------------------------------------------------

    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently authenticated user."""
        return self._current_user

    @current_user.setter
    def current_user(self, value: Optional[Dict[str, Any]]):
        """Set authenticated user and emit signal."""
        self._current_user = value
        if value:
            self.user_changed.emit(value)

    # >>> FIX YOU NEED <<<
    def set_logged_in_user(self, user_data: Dict[str, Any]):
        """Compatibility method expected by login logic."""
        self.current_user = user_data

    def get_logged_in_user(self) -> Optional[Dict[str, Any]]:
        return self.current_user
    # <<< FIX DONE <<<

    # --------------------------------------------------------------------------
    # API CLIENT STATE
    # --------------------------------------------------------------------------

    @property
    def api_client(self) -> Optional[Any]:
        return self._api_client

    @api_client.setter
    def api_client(self, value: Optional[Any]):
        self._api_client = value

    # --------------------------------------------------------------------------
    # APPEARANCE MODE STATE
    # --------------------------------------------------------------------------

    @property
    def is_dark_mode(self) -> bool:
        return self._is_dark_mode

    @is_dark_mode.setter
    def is_dark_mode(self, value: bool):
        self._is_dark_mode = value
        self.theme_changed.emit(value)

    # --------------------------------------------------------------------------
    # SELECTION STATE
    # --------------------------------------------------------------------------

    @property
    def selected_product_id(self) -> Optional[int]:
        return self._selected_product_id

    @selected_product_id.setter
    def selected_product_id(self, value: Optional[int]):
        self._selected_product_id = value
        if value:
            self.product_selected.emit(value)

    @property
    def selected_category_id(self) -> Optional[int]:
        return self._selected_category_id

    @selected_category_id.setter
    def selected_category_id(self, value: Optional[int]):
        self._selected_category_id = value

    # --------------------------------------------------------------------------

    def clear_state(self):
        """Clear all app state (logout)."""
        self._current_user = None
        self._api_client = None
        self._selected_product_id = None
        self._selected_category_id = None
        self._notifications.clear()


# --------------------------------------------------------------------------
# SINGLETON ACCESS — DO NOT TOUCH
# --------------------------------------------------------------------------

_app_state: Optional[AppState] = None


def get_app_state() -> AppState:
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state


# Convenience wrappers
def get_current_user():
    return get_app_state().current_user


def set_current_user(user):
    get_app_state().current_user = user


def get_api_client():
    return get_app_state().api_client


def set_api_client(client):
    get_app_state().api_client = client


def clear_app_state():
    get_app_state().clear_state()
