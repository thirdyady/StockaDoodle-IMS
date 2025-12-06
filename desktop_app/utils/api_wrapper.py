# desktop_app/utils/api_wrapper.py
# Convenience singleton bridge to the StockaDoodleAPI client.
# UI modules import these functions to interact with the API without
# managing client instances.

from typing import Optional, Dict, List, Any

# ✅ FIXED IMPORTS: use desktop_app.utils.*, not bare utils.*
from desktop_app.utils.config import AppConfig
from desktop_app.utils.app_state import get_current_user

_api_client = None


def get_api():
    """
    Get or create the singleton API client instance.
    Returns:
        StockaDoodleAPI: The API client instance
    """
    global _api_client
    if _api_client is None:
        # import here to avoid circular imports at module import time
        from desktop_app.api_client.stockadoodle_api import StockaDoodleAPI
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
    """Reset the API client instance."""
    global _api_client
    _api_client = None


# -----------------------
# Authentication helpers
# -----------------------

def login(username: str, password: str) -> Dict:
    """
    Login and authenticate user.
    Returns the API response dict (may include mfa_required).
    """
    api = get_api()
    return api.login(username, password)


def send_mfa_code(username: str, email: str) -> Dict:
    """Send MFA code to email"""
    api = get_api()
    return api.send_mfa_code(username, email)


def verify_mfa(username: str, code: str) -> Dict:
    """Verify MFA code and complete login"""
    api = get_api()
    return api.verify_mfa_code(username, code)


def logout():
    """Logout and reset API client."""
    api = get_api()
    api.logout()
    reset_api()


# -----------------------
# Products & categories
# -----------------------

def get_products(page: int = 1, per_page: int = 10,
                 include_image: bool = False, name: Optional[str] = None,
                 brand: Optional[str] = None, category_id: Optional[int] = None,
                 **extra_filters) -> Dict:
    """
    Get a paginated list of products.
    Accepts common filters (name, brand, category_id) and forwards any extra filters.
    Returns the raw API response (dict).
    """
    api = get_api()
    filters = dict(extra_filters)
    if name:
        filters['name'] = name
    if brand:
        filters['brand'] = brand
    if category_id is not None:
        filters['category_id'] = category_id

    return api.get_products(page=page, per_page=per_page, include_image=include_image, **filters)


def get_product(product_id: int, include_image: bool = False, include_batches: bool = False) -> Dict:
    """Get a single product by ID (with optional image and batch data)."""
    api = get_api()
    return api.get_product(product_id, include_image=include_image, include_batches=include_batches)


def create_product(product_data: Dict[str, Any]) -> Dict:
    """
    Create a new product.
    product_data should match the parameters expected by StockaDoodleAPI.create_product
    (e.g. name, price, brand, category_id, product_image (bytes), etc.)
    """
    api = get_api()
    return api.create_product(**product_data)


def update_product(product_id: int, product_data: Dict[str, Any]) -> Dict:
    """Update an existing product (partial update)."""
    api = get_api()
    return api.update_product(product_id, **product_data)


def delete_product(product_id: int, user_id: Optional[int] = None) -> Dict:
    """Delete a product. user_id optionally identifies the actor."""
    api = get_api()
    return api.delete_product(product_id, user_id=user_id)


def get_categories(include_image: bool = False) -> List[Dict]:
    """Get all categories."""
    api = get_api()
    return api.get_categories(include_image=include_image)


def get_category(category_id: int, include_image: bool = False) -> Dict:
    """Get a single category by ID."""
    api = get_api()
    return api.get_category(category_id, include_image=include_image)


def create_category(category_data: Dict[str, Any]) -> Dict:
    """Create a new category. category_data should match create_category args."""
    api = get_api()
    return api.create_category(**category_data)


def update_category(category_id: int, category_data: Dict[str, Any]) -> Dict:
    """Update a category (partial)."""
    api = get_api()
    return api.update_category(category_id, **category_data)


def delete_category(category_id: int) -> Dict:
    """Delete a category."""
    api = get_api()
    return api.delete_category(category_id)


# -----------------------
# Stock batches
# -----------------------

def get_stock_batches(product_id: int) -> Dict:
    """Get stock batches for a product."""
    api = get_api()
    return api.get_stock_batches(product_id)


def add_stock_batch(product_id: int, batch_data: Dict[str, Any]) -> Dict:
    """
    Add a new stock batch.
    batch_data should include: quantity, expiration_date (ISO str), optional reason, added_by
    """
    api = get_api()
    return api.add_stock_batch(product_id, **batch_data)


def delete_stock_batch(product_id: int, batch_id: int, user_id: Optional[int] = None) -> Dict:
    """Delete a stock batch."""
    api = get_api()
    return api.delete_stock_batch(product_id, batch_id, user_id=user_id)


def dispose_product(product_id: int, quantity: int, reason: str, user_id: Optional[int] = None) -> Dict:
    """
    Dispose product stock (FEFO).
    Note: the underlying API expects product_id and quantity; batch-level dispose logic is handled server-side.
    """
    api = get_api()
    return api.dispose_product(product_id, quantity=quantity, reason=reason, user_id=user_id)


# -----------------------
# Sales
# -----------------------

def record_sale(retailer_id: int, items: List[Dict[str, Any]], total_amount: float) -> Dict:
    """
    Record a sale.
    items should be a list of dicts with keys: product_id, quantity, line_total
    """
    api = get_api()
    return api.record_sale(retailer_id, items, total_amount)


def get_sales(start_date: Optional[str] = None, end_date: Optional[str] = None,
              retailer_id: Optional[int] = None) -> Dict:
    """Get sales records with optional date and retailer filters."""
    api = get_api()
    return api.get_sales(start_date=start_date, end_date=end_date, retailer_id=retailer_id)


def get_sale(sale_id: int, include_items: bool = True) -> Dict:
    """Get a single sale by ID."""
    api = get_api()
    return api.get_sale(sale_id, include_items=include_items)


def undo_sale(sale_id: int, user_id: Optional[int] = None) -> Dict:
    """Undo a sale (admin only)."""
    api = get_api()
    return api.undo_sale(sale_id, user_id=user_id)


# -----------------------
# Logs, reports & metrics
# -----------------------

def get_product_logs(product_id: int, limit: int = 100) -> Dict:
    api = get_api()
    return api.get_product_logs(product_id, limit=limit)


def get_user_logs(user_id: int, limit: int = 100) -> Dict:
    api = get_api()
    return api.get_user_logs(user_id, limit=limit)


def get_all_logs(action_type: Optional[str] = None, limit: int = 100) -> Dict:
    api = get_api()
    return api.get_all_logs(action_type=action_type, limit=limit)


def get_disposal_report(start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 100) -> Dict:
    api = get_api()
    return api.get_disposal_report(start_date=start_date, end_date=end_date, limit=limit)


def get_api_logs(method: Optional[str] = None, target_entity: Optional[str] = None, limit: int = 100) -> Dict:
    api = get_api()
    return api.get_api_logs(method=method, target_entity=target_entity, limit=limit)


def get_retailer_metrics(user_id: int) -> Dict:
    api = get_api()
    return api.get_retailer_metrics(user_id)


def get_leaderboard(limit: int = 10) -> Dict:
    api = get_api()
    return api.get_leaderboard(limit=limit)


def get_all_metrics() -> Dict:
    api = get_api()
    return api.get_all_metrics()


def update_retailer_quota(user_id: int, new_quota: float, updated_by: Optional[int] = None) -> Dict:
    api = get_api()
    return api.update_retailer_quota(user_id, new_quota, updated_by=updated_by)


def get_sales_performance_report(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    api = get_api()
    return api.get_sales_performance_report(start_date=start_date, end_date=end_date)


def get_detailed_transaction_report(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    api = get_api()
    return api.get_detailed_transaction_report(start_date=start_date, end_date=end_date)


def get_user_accounts_report() -> Dict:
    api = get_api()
    return api.get_user_accounts_report()


def download_pdf_report(report_type: str, **params) -> bytes:
    api = get_api()
    return api.download_pdf_report(report_type, **params)


# Notifications & health
def send_low_stock_alerts(triggered_by: int = None) -> Dict:
    api = get_api()
    return api.send_low_stock_alerts(triggered_by=triggered_by)


def send_expiration_alerts(days_ahead: int = 7, triggered_by: int = None) -> Dict:
    api = get_api()
    return api.send_expiration_alerts(days_ahead=days_ahead, triggered_by=triggered_by)


def send_daily_summary(triggered_by: int = None) -> Dict:
    api = get_api()
    return api.send_daily_summary(triggered_by=triggered_by)


def get_notification_history(limit: int = 50, notification_type: str = None) -> Dict:
    api = get_api()
    return api.get_notification_history(limit=limit, notification_type=notification_type)


def health_check() -> Dict:
    api = get_api()
    return api.health_check()


# -----------------------
# Current user helper
# -----------------------

def get_current_user_data() -> Optional[Dict]:
    api = get_api()
    if getattr(api, 'current_user', None):
        return api.current_user
    return get_current_user()
