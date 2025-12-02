# app_state.py
#
# This module manages global application state that needs to be accessed
# across multiple UI components and modules.
#
# Usage: Imported by UI modules to access and modify global application state.

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal


class AppState(QObject):
    """
    Singleton class for managing global application state.
    Uses Qt signals for state change notifications.
    """
    
    # Signals emitted when state changes
    user_changed = pyqtSignal(dict)  # Emitted when current_user changes
    theme_changed = pyqtSignal(bool)  # Emitted when theme changes (True = dark)
    product_selected = pyqtSignal(int)  # Emitted when a product is selected
    
    def __init__(self):
        super().__init__()
        self._current_user: Optional[Dict[str, Any]] = None
        self._api_client: Optional[Any] = None
        self._is_dark_mode: bool = True
        self._selected_product_id: Optional[int] = None
        self._selected_category_id: Optional[int] = None
        self._notifications: list = []
        
    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user."""
        return self._current_user
    
    @current_user.setter
    def current_user(self, value: Optional[Dict[str, Any]]):
        """Set the current authenticated user and emit signal."""
        self._current_user = value
        if value:
            self.user_changed.emit(value)
    
    @property
    def api_client(self) -> Optional[Any]:
        """Get the API client instance."""
        return self._api_client
    
    @api_client.setter
    def api_client(self, value: Optional[Any]):
        """Set the API client instance."""
        self._api_client = value
    
    @property
    def is_dark_mode(self) -> bool:
        """Check if dark mode is enabled."""
        return self._is_dark_mode
    
    @is_dark_mode.setter
    def is_dark_mode(self, value: bool):
        """Set dark mode and emit signal."""
        self._is_dark_mode = value
        self.theme_changed.emit(value)
    
    @property
    def selected_product_id(self) -> Optional[int]:
        """Get the currently selected product ID."""
        return self._selected_product_id
    
    @selected_product_id.setter
    def selected_product_id(self, value: Optional[int]):
        """Set the selected product ID and emit signal."""
        self._selected_product_id = value
        if value:
            self.product_selected.emit(value)
    
    @property
    def selected_category_id(self) -> Optional[int]:
        """Get the currently selected category ID."""
        return self._selected_category_id
    
    @selected_category_id.setter
    def selected_category_id(self, value: Optional[int]):
        """Set the selected category ID."""
        self._selected_category_id = value
    
    def clear_state(self):
        """Clear all application state (useful for logout)."""
        self._current_user = None
        self._api_client = None
        self._selected_product_id = None
        self._selected_category_id = None
        self._notifications.clear()


# Singleton instance
_app_state: Optional[AppState] = None


def get_app_state() -> AppState:
    """
    Get the singleton AppState instance.
    
    Returns:
        AppState: The global application state instance
    """
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state


# Convenience functions for common state operations

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current authenticated user."""
    return get_app_state().current_user


def set_current_user(user: Optional[Dict[str, Any]]):
    """Set the current authenticated user."""
    get_app_state().current_user = user


def get_api_client():
    """Get the API client instance."""
    return get_app_state().api_client


def set_api_client(client):
    """Set the API client instance."""
    get_app_state().api_client = client


def is_dark_mode() -> bool:
    """Check if dark mode is enabled."""
    return get_app_state().is_dark_mode


def set_dark_mode(enabled: bool):
    """Enable or disable dark mode."""
    get_app_state().is_dark_mode = enabled


def get_selected_product_id() -> Optional[int]:
    """Get the currently selected product ID."""
    return get_app_state().selected_product_id


def set_selected_product_id(product_id: Optional[int]):
    """Set the selected product ID."""
    get_app_state().selected_product_id = product_id


def get_selected_category_id() -> Optional[int]:
    """Get the currently selected category ID."""
    return get_app_state().selected_category_id


def set_selected_category_id(category_id: Optional[int]):
    """Set the selected category ID."""
    get_app_state().selected_category_id = category_id


def clear_app_state():
    """Clear all application state."""
    get_app_state().clear_state()

