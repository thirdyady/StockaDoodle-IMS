# api_wrapper.py
#
# This module provides a convenience wrapper around the StockaDoodleAPI client.
# Acts as a singleton bridge to the API client for easy access throughout the app.
#
# Usage: Imported by UI modules to make API calls without managing API client instances.

from typing import Optional
from utils.config import AppConfig
from utils.app_state import get_current_user


# Singleton API client instance
_api_client = None


def get_api():
    """
    Get or create the singleton API client instance.
    
    Returns:
        StockaDoodleAPI: The API client instance
    """
    global _api_client
    
    if _api_client is None:
        from api_client.stockadoodle_api import StockaDoodleAPI
        _api_client = StockaDoodleAPI(base_url=AppConfig.API_BASE_URL)
    
    return _api_client


def set_api(api_client):
    """
    Set the API client instance (useful for testing or re-authentication).
    
    Args:
        api_client: The StockaDoodleAPI instance to use
    """
    global _api_client
    _api_client = api_client


def reset_api():
    """Reset the API client instance (useful for logout)."""
    global _api_client
    _api_client = None


# Convenience functions for common API operations

def login(username: str, password: str) -> dict:
    """Login and authenticate user."""
    api = get_api()
    return api.login(username, password)


def logout():
    """Logout and reset API client."""
    reset_api()


def get_products(search: str = None, category_id: int = None, **kwargs) -> list:
    """Get list of products with optional filters."""
    api = get_api()
    return api.get_products(search=search, category_id=category_id, **kwargs)


def get_product(product_id: int) -> dict:
    """Get a single product by ID."""
    api = get_api()
    return api.get_product(product_id)


def create_product(product_data: dict) -> dict:
    """Create a new product."""
    api = get_api()
    return api.create_product(**product_data)


def update_product(product_id: int, product_data: dict) -> dict:
    """Update an existing product."""
    api = get_api()
    return api.update_product(product_id, **product_data)


def delete_product(product_id: int) -> bool:
    """Delete a product."""
    api = get_api()
    return api.delete_product(product_id)


def get_stock_batches(product_id: int) -> list:
    """Get stock batches for a product."""
    api = get_api()
    return api.get_stock_batches(product_id)


def add_stock_batch(product_id: int, batch_data: dict) -> dict:
    """Add a new stock batch."""
    api = get_api()
    return api.add_stock_batch(product_id, **batch_data)


def dispose_product(product_id: int, batch_id: int, quantity: int, reason: str) -> dict:
    """Dispose of damaged/expired products."""
    api = get_api()
    return api.dispose_product(product_id, batch_id, quantity, reason)


def record_sale(product_id: int, quantity: int, total_price: float) -> dict:
    """Record a sale."""
    api = get_api()
    user = get_current_user()
    seller_id = user.get('id') if user else None
    return api.record_sale(product_id, quantity, total_price, seller_id)


def get_sales(start_date: str = None, end_date: str = None, **kwargs) -> list:
    """Get sales records with optional date filters."""
    api = get_api()
    return api.get_sales(start_date=start_date, end_date=end_date, **kwargs)


def get_categories() -> list:
    """Get all categories."""
    api = get_api()
    return api.get_categories()


def get_product_logs(product_id: int, limit: int = 100) -> list:
    """Get product activity logs."""
    api = get_api()
    return api.get_product_logs(product_id, limit=limit)


def get_current_user_data() -> Optional[dict]:
    """Get current authenticated user data."""
    api = get_api()
    if api.current_user:
        return api.current_user
    return get_current_user()


def verify_mfa(username: str, code: str) -> bool:
    """Verify MFA code."""
    api = get_api()
    return api.verify_mfa(username, code)

