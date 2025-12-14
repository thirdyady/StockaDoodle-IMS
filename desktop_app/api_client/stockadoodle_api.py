# desktop_app/api_client/stockadoodle_api.py

from __future__ import annotations

import requests
from typing import Optional, Dict, List, Any, Union

from desktop_app.utils.config import AppConfig


class StockaDoodleAPIError(Exception):
    """Generic API error for the desktop client."""
    pass


class StockaDoodleAPI:
    """
    Client-side API wrapper for StockaDoodle IMS.
    Handles HTTP requests to the Flask backend.

    Notes:
    - _request() supports JSON by default.
    - For PDF or other binary responses, use raw=True or call download_pdf_report().
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None
    ):
        self.base_url = base_url or AppConfig.API_BASE_URL
        self.timeout = timeout or AppConfig.API_TIMEOUT

        self.session = requests.Session()
        self.current_user: Optional[Dict[str, Any]] = None

    # ----------------------------
    # Core request helpers
    # ----------------------------
    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _request(
        self,
        method: str,
        endpoint: str,
        raw: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], bytes]:
        """
        Core request handler.

        Args:
            method: HTTP method
            endpoint: API endpoint
            raw: If True, returns bytes without JSON parsing.
            **kwargs: forwarded to requests.Session.request()

        Returns:
            dict (JSON) by default, or bytes if raw=True or response is PDF.
        """
        url = self._url(endpoint)

        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        try:
            response = self.session.request(method, url, **kwargs)

            content_type = (response.headers.get("Content-Type") or "").lower()
            is_pdf = "application/pdf" in content_type

            if not response.ok:
                try:
                    data = response.json()
                except Exception:
                    data = None

                if isinstance(data, dict):
                    errors = data.get("errors")
                    if isinstance(errors, list) and errors:
                        raise StockaDoodleAPIError(str(errors[0]))
                    message = data.get("message")
                    if message:
                        raise StockaDoodleAPIError(str(message))

                raise StockaDoodleAPIError(
                    f"HTTP {response.status_code}: {response.reason}"
                )

            if raw or is_pdf:
                return response.content

            try:
                data = response.json()
            except Exception:
                data = None

            return data or {}

        except requests.exceptions.RequestException as e:
            raise StockaDoodleAPIError(f"Connection error: {str(e)}")

    # ================================================================
    # AUTHENTICATION & USER MANAGEMENT
    # ================================================================
    def login(self, username: str, password: str) -> Dict[str, Any]:
        data = {"username": username, "password": password}
        result = self._request("POST", "/users/auth/login", json=data)

        if isinstance(result, dict) and not result.get("mfa_required"):
            self.current_user = result.get("user")

        return result  # type: ignore[return-value]

    def send_mfa_code(self, username: str, email: str) -> Dict[str, Any]:
        data = {"username": username, "email": email}
        result = self._request("POST", "/users/auth/mfa/send", json=data)
        return result  # type: ignore[return-value]

    def verify_mfa_code(self, username: str, code: str) -> Dict[str, Any]:
        data = {"username": username, "code": code}
        result = self._request("POST", "/users/auth/mfa/verify", json=data)
        if isinstance(result, dict):
            self.current_user = result.get("user")
        return result  # type: ignore[return-value]

    def logout(self):
        self.current_user = None

    # ================================================================
    # USER MANAGEMENT
    # ================================================================
    def get_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"role": role} if role else {}
        result = self._request("GET", "/users", params=params)
        if isinstance(result, dict):
            return result.get("users", [])
        return []

    def get_user(self, user_id: int, include_image: bool = False) -> Dict[str, Any]:
        params = {"include_image": "true"} if include_image else {}
        result = self._request("GET", f"/users/{user_id}", params=params)
        return result  # type: ignore[return-value]

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        role: str = "staff",
        user_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "username": username,
            "password": password,
            "full_name": full_name,
            "email": email,
            "role": role,
        }
        if user_image:
            data["image_data"] = user_image

        result = self._request("POST", "/users", json=data)
        return result  # type: ignore[return-value]

    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        result = self._request("PATCH", f"/users/{user_id}", json=kwargs)
        return result  # type: ignore[return-value]

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        result = self._request("DELETE", f"/users/{user_id}")
        return result  # type: ignore[return-value]

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        data = {"old_password": old_password, "new_password": new_password}
        result = self._request("POST", f"/users/{user_id}/change-password", json=data)
        return result  # type: ignore[return-value]

    # ================================================================
    # CATEGORY MANAGEMENT
    # ================================================================
    def get_categories(self, include_image: bool = False) -> List[Dict[str, Any]]:
        params = {"include_image": "true"} if include_image else {}
        result = self._request("GET", "/categories", params=params)
        if isinstance(result, dict):
            return result.get("categories", [])
        return []

    def get_category(self, category_id: int, include_image: bool = False) -> Dict[str, Any]:
        params = {"include_image": "true"} if include_image else {}
        result = self._request("GET", f"/categories/{category_id}", params=params)
        return result  # type: ignore[return-value]

    def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        category_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"name": name, "description": description}
        data = {k: v for k, v in data.items() if v is not None}

        if category_image:
            data["image_data"] = category_image

        result = self._request("POST", "/categories", json=data)
        return result  # type: ignore[return-value]

    def update_category(self, category_id: int, **kwargs) -> Dict[str, Any]:
        result = self._request("PATCH", f"/categories/{category_id}", json=kwargs)
        return result  # type: ignore[return-value]

    def delete_category(self, category_id: int) -> Dict[str, Any]:
        result = self._request("DELETE", f"/categories/{category_id}")
        return result  # type: ignore[return-value]

    # ================================================================
    # PRODUCT MANAGEMENT
    # ================================================================
    def get_products(
        self,
        page: int = 1,
        per_page: int = 10,
        include_image: bool = False,
        **filters
    ) -> Dict[str, Any]:
        params = {
            "page": page,
            "per_page": per_page,
            "include_image": "true" if include_image else "false",
            **filters,
        }
        result = self._request("GET", "/products", params=params)
        return result  # type: ignore[return-value]

    def get_product(
        self,
        product_id: int,
        include_image: bool = False,
        include_batches: bool = False
    ) -> Dict[str, Any]:
        params = {
            "include_image": "true" if include_image else "false",
            "include_batches": "true" if include_batches else "false",
        }
        result = self._request("GET", f"/products/{product_id}", params=params)
        return result  # type: ignore[return-value]

    def create_product(
        self,
        name: str,
        price: float,
        brand: Optional[str] = None,
        category_id: Optional[int] = None,
        min_stock_level: int = 10,
        details: Optional[str] = None,
        product_image: Optional[bytes] = None,
        stock_level: Optional[int] = None,
        expiration_date: Optional[str] = None,
        added_by: Optional[int] = None
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": name,
            "price": price,
            "brand": brand,
            "category_id": category_id,
            "min_stock_level": min_stock_level,
            "details": details,
            "stock_level": stock_level,
            "expiration_date": expiration_date,
            "added_by": added_by or (self.current_user["id"] if self.current_user else None),
        }

        data = {k: v for k, v in data.items() if v is not None}

        if product_image:
            data["image_data"] = product_image

        result = self._request("POST", "/products", json=data)
        return result  # type: ignore[return-value]

    def update_product(self, product_id: int, **kwargs) -> Dict[str, Any]:
        if self.current_user and "added_by" not in kwargs:
            kwargs["added_by"] = self.current_user["id"]
        result = self._request("PATCH", f"/products/{product_id}", json=kwargs)
        return result  # type: ignore[return-value]

    def delete_product(self, product_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        data = {"user_id": user_id or (self.current_user["id"] if self.current_user else None)}
        result = self._request("DELETE", f"/products/{product_id}", json=data)
        return result  # type: ignore[return-value]

    # ================================================================
    # STOCK BATCH MANAGEMENT
    # ================================================================
    def get_stock_batches(self, product_id: int) -> Dict[str, Any]:
        result = self._request("GET", f"/products/{product_id}/stock_batches")
        return result  # type: ignore[return-value]

    def add_stock_batch(
        self,
        product_id: int,
        quantity: int,
        expiration_date: str,
        reason: str = "Stock added",
        added_by: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {
            "quantity": quantity,
            "expiration_date": expiration_date,
            "reason": reason,
            "added_by": added_by or (self.current_user["id"] if self.current_user else None),
        }
        result = self._request("POST", f"/products/{product_id}/stock_batches", json=data)
        return result  # type: ignore[return-value]

    def dispose_product(
        self,
        product_id: int,
        quantity: int,
        reason: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        # Server expects product_id + user_id + quantity + notes
        data = {
            "product_id": product_id,
            "quantity": quantity,
            "user_id": user_id or (self.current_user["id"] if self.current_user else None),
            "notes": reason,
        }
        result = self._request("POST", "/log/dispose", json=data)
        return result  # type: ignore[return-value]

    def delete_stock_batch(
        self,
        product_id: int,
        batch_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {"user_id": user_id or (self.current_user["id"] if self.current_user else None)}
        result = self._request("DELETE", f"/products/{product_id}/stock_batches/{batch_id}", json=data)
        return result  # type: ignore[return-value]

    # ================================================================
    # SALES MANAGEMENT
    # ================================================================
    def record_sale(self, retailer_id: int, items: List[Dict[str, Any]], total_amount: float) -> Dict[str, Any]:
        data = {"retailer_id": retailer_id, "items": items, "total_amount": total_amount}
        result = self._request("POST", "/sales", json=data)
        return result  # type: ignore[return-value]

    def get_sales(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        retailer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if retailer_id is not None:
            params["retailer_id"] = retailer_id

        result = self._request("GET", "/sales/reports", params=params)
        return result  # type: ignore[return-value]

    def get_sale(self, sale_id: int, include_items: bool = True) -> Dict[str, Any]:
        params = {"include_items": "true" if include_items else "false"}
        result = self._request("GET", f"/sales/{sale_id}", params=params)
        return result  # type: ignore[return-value]

    def undo_sale(self, sale_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        data = {"user_id": user_id or (self.current_user["id"] if self.current_user else None)}
        result = self._request("DELETE", f"/sales/{sale_id}", json=data)
        return result  # type: ignore[return-value]

    # ✅ NEW: Return ONE sold item row inside a Sale (sale_id + item_index)
    def return_sale_item(self, sale_id: int, item_index: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        data = {"user_id": user_id or (self.current_user["id"] if self.current_user else None)}
        result = self._request("DELETE", f"/sales/{sale_id}/items/{item_index}", json=data)
        return result  # type: ignore[return-value]

    # ================================================================
    # LOGS & AUDIT
    # ================================================================
    def get_product_logs(self, product_id: int, limit: int = 50) -> Dict[str, Any]:
        result = self._request("GET", f"/log/product/{product_id}", params={"limit": limit})
        return result  # type: ignore[return-value]

    def get_user_logs(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        result = self._request("GET", f"/log/user/{user_id}", params={"limit": limit})
        return result  # type: ignore[return-value]

    def get_all_logs(self, action_type: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        params = {"limit": limit}
        if action_type:
            params["action_type"] = action_type
        result = self._request("GET", "/log", params=params)
        return result  # type: ignore[return-value]

    def get_api_logs(
        self,
        method: Optional[str] = None,
        target_entity: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit}
        if method:
            params["method"] = method
        if target_entity:
            params["target_entity"] = target_entity
        result = self._request("GET", "/log/api", params=params)
        return result  # type: ignore[return-value]

    # ================================================================
    # DASHBOARD (new)
    # ================================================================
    def get_admin_dashboard(self) -> Dict[str, Any]:
        """Admin dashboard metrics."""
        result = self._request("GET", "/dashboard/admin")
        return result  # type: ignore[return-value]

    def get_manager_dashboard(self) -> Dict[str, Any]:
        """Manager dashboard metrics."""
        result = self._request("GET", "/dashboard/manager")
        return result  # type: ignore[return-value]

    def get_retailer_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Retailer dashboard metrics for a specific user."""
        result = self._request("GET", f"/dashboard/retailer/{user_id}")
        return result  # type: ignore[return-value]

    # ================================================================
    # METRICS
    # ================================================================
    def get_retailer_metrics(self, user_id: int) -> Dict[str, Any]:
        result = self._request("GET", f"/retailer/{user_id}")
        return result  # type: ignore[return-value]

    def get_leaderboard(self, limit: int = 10) -> Dict[str, Any]:
        result = self._request("GET", "/retailer/leaderboard", params={"limit": limit})
        return result  # type: ignore[return-value]

    def get_all_metrics(self) -> Dict[str, Any]:
        result = self._request("GET", "/metrics/all")
        return result  # type: ignore[return-value]

    def update_retailer_quota(
        self,
        user_id: int,
        new_quota: float,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {
            "new_quota": new_quota,
            "updated_by": updated_by or (self.current_user["id"] if self.current_user else None),
        }
        result = self._request("PATCH", f"/metrics/retailer/{user_id}/quota", json=data)
        return result  # type: ignore[return-value]

    # ================================================================
    # REPORTS (JSON endpoints)
    # ================================================================
    def get_sales_performance_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        result = self._request("GET", "/reports/sales-performance", params=params)
        return result  # type: ignore[return-value]

    def get_category_distribution_report(self) -> Dict[str, Any]:
        result = self._request("GET", "/reports/category-distribution")
        return result  # type: ignore[return-value]

    def get_retailer_performance_report(self) -> Dict[str, Any]:
        result = self._request("GET", "/reports/retailer-performance")
        return result  # type: ignore[return-value]

    def get_alerts_report(self, days_ahead: int = 7) -> Dict[str, Any]:
        result = self._request("GET", "/reports/alerts", params={"days_ahead": days_ahead})
        return result  # type: ignore[return-value]

    def get_managerial_activity_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        result = self._request("GET", "/reports/managerial-activity", params=params)
        return result  # type: ignore[return-value]

    def get_detailed_transaction_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        result = self._request("GET", "/reports/transactions", params=params)
        return result  # type: ignore[return-value]

    def get_user_accounts_report(self) -> Dict[str, Any]:
        result = self._request("GET", "/reports/user-accounts")
        return result  # type: ignore[return-value]

    # ================================================================
    # REPORTS (PDF download)
    # ================================================================
    def download_pdf_report(self, report_type: str, **params) -> bytes:
        result = self._request(
            "GET",
            f"/reports/{report_type}/pdf",
            params=params or None,
            raw=True
        )
        if isinstance(result, (bytes, bytearray)):
            return bytes(result)
        raise StockaDoodleAPIError("PDF download failed: response was not bytes.")

    # ================================================================
    # NOTIFICATIONS
    # ================================================================
    def send_low_stock_alerts(self, triggered_by: Optional[int] = None) -> Dict[str, Any]:
        result = self._request(
            "POST",
            "/notifications/low-stock",
            json={"triggered_by": triggered_by},
        )
        return result  # type: ignore[return-value]

    def send_expiration_alerts(
        self,
        days_ahead: int = 7,
        triggered_by: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {"days_ahead": days_ahead, "triggered_by": triggered_by}
        result = self._request("POST", "/notifications/expiring", json=data)
        return result  # type: ignore[return-value]

    def send_daily_summary(self, triggered_by: Optional[int] = None) -> Dict[str, Any]:
        result = self._request(
            "POST",
            "/notifications/daily-summary",
            json={"triggered_by": triggered_by},
        )
        return result  # type: ignore[return-value]

    def get_notification_history(
        self,
        limit: int = 50,
        notification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"limit": limit}
        if notification_type:
            params["notification_type"] = notification_type
        result = self._request("GET", "/notifications/history", params=params)
        return result  # type: ignore[return-value]

    # ================================================================
    # HEALTH CHECK
    # ================================================================
    def health_check(self) -> Dict[str, Any]:
        result = self._request("GET", "/health")
        return result  # type: ignore[return-value]
