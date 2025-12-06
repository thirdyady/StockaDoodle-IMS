# desktop_app/api_client/stockadoodle_api.py

from __future__ import annotations

import requests
from typing import Optional, Dict, List, Any

from desktop_app.utils.config import AppConfig


class StockaDoodleAPIError(Exception):
    """Generic API error for the desktop client."""
    pass


class StockaDoodleAPI:
    """
    Client-side API wrapper for StockaDoodle IMS.
    Handles HTTP requests to the Flask backend.
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

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = self._url(endpoint)

        # Ensure timeout is always applied unless explicitly overridden
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        try:
            response = self.session.request(method, url, **kwargs)

            # Try to parse json even on error for better messages
            try:
                data = response.json()
            except Exception:
                data = None

            if not response.ok:
                # Backend often returns { "errors": [...] }
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

            # If ok but no json body
            if data is None:
                return {}

            return data

        except requests.exceptions.RequestException as e:
            raise StockaDoodleAPIError(f"Connection error: {str(e)}")

    # ================================================================
    # AUTHENTICATION & USER MANAGEMENT
    # ================================================================
    def login(self, username: str, password: str) -> Dict[str, Any]:
        data = {"username": username, "password": password}
        result = self._request("POST", "/users/auth/login", json=data)

        if not result.get("mfa_required"):
            self.current_user = result.get("user")

        return result

    def send_mfa_code(self, username: str, email: str) -> Dict[str, Any]:
        data = {"username": username, "email": email}
        return self._request("POST", "/users/auth/mfa/send", json=data)

    def verify_mfa_code(self, username: str, code: str) -> Dict[str, Any]:
        data = {"username": username, "code": code}
        result = self._request("POST", "/users/auth/mfa/verify", json=data)
        self.current_user = result.get("user")
        return result

    def logout(self):
        self.current_user = None

    # ================================================================
    # USER MANAGEMENT
    # ================================================================
    def get_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"role": role} if role else {}
        result = self._request("GET", "/users", params=params)
        return result.get("users", [])

    def get_user(self, user_id: int, include_image: bool = False) -> Dict[str, Any]:
        params = {"include_image": "true"} if include_image else {}
        return self._request("GET", f"/users/{user_id}", params=params)

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

        return self._request("POST", "/users", json=data)

    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        return self._request("PATCH", f"/users/{user_id}", json=kwargs)

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/users/{user_id}")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        data = {"old_password": old_password, "new_password": new_password}
        return self._request("POST", f"/users/{user_id}/change-password", json=data)

    # ================================================================
    # CATEGORY MANAGEMENT
    # ================================================================
    def get_categories(self, include_image: bool = False) -> List[Dict[str, Any]]:
        params = {"include_image": "true"} if include_image else {}
        result = self._request("GET", "/categories", params=params)
        return result.get("categories", [])

    def get_category(self, category_id: int, include_image: bool = False) -> Dict[str, Any]:
        params = {"include_image": "true"} if include_image else {}
        return self._request("GET", f"/categories/{category_id}", params=params)

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

        return self._request("POST", "/categories", json=data)

    def update_category(self, category_id: int, **kwargs) -> Dict[str, Any]:
        return self._request("PATCH", f"/categories/{category_id}", json=kwargs)

    def delete_category(self, category_id: int) -> Dict[str, Any]:
        return self._request("DELETE", f"/categories/{category_id}")

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
        return self._request("GET", "/products", params=params)

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
        return self._request("GET", f"/products/{product_id}", params=params)

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

        return self._request("POST", "/products", json=data)

    def update_product(self, product_id: int, **kwargs) -> Dict[str, Any]:
        if self.current_user and "added_by" not in kwargs:
            kwargs["added_by"] = self.current_user["id"]
        return self._request("PATCH", f"/products/{product_id}", json=kwargs)

    def delete_product(self, product_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        data = {"user_id": user_id or (self.current_user["id"] if self.current_user else None)}
        return self._request("DELETE", f"/products/{product_id}", json=data)

    # ================================================================
    # STOCK BATCH MANAGEMENT
    # ================================================================
    def get_stock_batches(self, product_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/products/{product_id}/stock_batches")

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
        return self._request("POST", f"/products/{product_id}/stock_batches", json=data)

    def dispose_product(
        self,
        product_id: int,
        quantity: int,
        reason: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {
            "quantity": quantity,
            "reason": reason,
            "user_id": user_id or (self.current_user["id"] if self.current_user else None),
        }
        return self._request("POST", "/log/dispose", json=data)

    def delete_stock_batch(
        self,
        product_id: int,
        batch_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {"user_id": user_id or (self.current_user["id"] if self.current_user else None)}
        return self._request("DELETE", f"/products/{product_id}/stock_batches/{batch_id}", json=data)

    # ================================================================
    # SALES MANAGEMENT
    # ================================================================
    def record_sale(self, retailer_id: int, items: List[Dict[str, Any]], total_amount: float) -> Dict[str, Any]:
        data = {"retailer_id": retailer_id, "items": items, "total_amount": total_amount}
        return self._request("POST", "/sales", json=data)

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
        if retailer_id:
            params["retailer_id"] = retailer_id

        return self._request("GET", "/sales/reports", params=params)

    def get_sale(self, sale_id: int, include_items: bool = True) -> Dict[str, Any]:
        params = {"include_items": "true" if include_items else "false"}
        return self._request("GET", f"/sales/{sale_id}", params=params)

    def undo_sale(self, sale_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        data = {"user_id": user_id or (self.current_user["id"] if self.current_user else None)}
        return self._request("DELETE", f"/sales/{sale_id}", json=data)

    # ================================================================
    # LOGS & AUDIT
    # ================================================================
    def get_product_logs(self, product_id: int, limit: int = 50) -> Dict[str, Any]:
        return self._request("GET", f"/log/product/{product_id}", params={"limit": limit})

    def get_user_logs(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        return self._request("GET", f"/log/user/{user_id}", params={"limit": limit})

    def get_all_logs(self, action_type: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        params = {"limit": limit}
        if action_type:
            params["action_type"] = action_type
        return self._request("GET", "/log", params=params)

    def get_disposal_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._request("GET", "/log/disposal", params=params)

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
        return self._request("GET", "/log/api", params=params)

    # ================================================================
    # METRICS
    # ================================================================
    def get_retailer_metrics(self, user_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/retailer/{user_id}")

    def get_leaderboard(self, limit: int = 10) -> Dict[str, Any]:
        return self._request("GET", "/retailer/leaderboard", params={"limit": limit})

    def get_all_metrics(self) -> Dict[str, Any]:
        return self._request("GET", "/metrics/all")

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
        return self._request("PATCH", f"/metrics/retailer/{user_id}/quota", json=data)

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
        return self._request("GET", "/reports/sales-performance", params=params)

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
        return self._request("GET", "/reports/transactions", params=params)

    def get_user_accounts_report(self) -> Dict[str, Any]:
        return self._request("GET", "/reports/user-accounts")

    # ================================================================
    # REPORTS (PDF download)
    # ================================================================
    def download_pdf_report(self, report_type: str, **params) -> bytes:
        """
        Download PDF report from: /reports/<type>/pdf
        Returns raw bytes.
        """
        url = self._url(f"/reports/{report_type}/pdf")

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            if not response.ok:
                raise StockaDoodleAPIError(
                    f"Failed to download PDF: HTTP {response.status_code}"
                )
            return response.content
        except requests.exceptions.RequestException as e:
            raise StockaDoodleAPIError(f"Connection error: {str(e)}")

    # ================================================================
    # NOTIFICATIONS
    # ================================================================
    def send_low_stock_alerts(self, triggered_by: Optional[int] = None) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/notifications/low-stock",
            json={"triggered_by": triggered_by},
        )

    def send_expiration_alerts(
        self,
        days_ahead: int = 7,
        triggered_by: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {"days_ahead": days_ahead, "triggered_by": triggered_by}
        return self._request("POST", "/notifications/expiring", json=data)

    def send_daily_summary(self, triggered_by: Optional[int] = None) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/notifications/daily-summary",
            json={"triggered_by": triggered_by},
        )

    def get_notification_history(
        self,
        limit: int = 50,
        notification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"limit": limit}
        if notification_type:
            params["notification_type"] = notification_type
        return self._request("GET", "/notifications/history", params=params)

    # ================================================================
    # HEALTH CHECK
    # ================================================================
    def health_check(self) -> Dict[str, Any]:
        return self._request("GET", "/health")
