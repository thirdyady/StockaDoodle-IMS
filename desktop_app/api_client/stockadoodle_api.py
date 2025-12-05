import requests  
import json  
from typing import Optional, Dict, List, Any  
from datetime import datetime  
  
  
class StockaDoodleAPI:  
    """  
    Client-side API wrapper for StockaDoodle IMS v3  
    Handles all HTTP requests to the Flask backend  
    """  
      
    def __init__(self, base_url: str = "http://127.0.0.1:5000/api/v1"):  
        """  
        Initialize API client  
          
        Args:  
            base_url: Base URL of the API server  
        """  
        self.base_url = base_url  
        self.session = requests.Session()  
        self.current_user = None  
        self.auth_token = None  
      
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:  
        """  
        Internal method to make HTTP requests  
          
        Args:  
            method: HTTP method (GET, POST, PATCH, PUT, DELETE)  
            endpoint: API endpoint (without base URL)  
            **kwargs: Additional arguments for requests  
              
        Returns:  
            dict: Response JSON data  
              
        Raises:  
            requests.exceptions.RequestException: On request failure  
        """  
        url = f"{self.base_url}/{endpoint.lstrip('/')}"  
          
        try:  
            response = self.session.request(method, url, **kwargs)  
            response.raise_for_status()  
            return response.json()  
        except requests.exceptions.HTTPError as e:  
            # Try to extract error message from response  
            try:  
                error_data = e.response.json()  
                raise Exception(error_data.get('errors', [str(e)])[0])  
            except:  
                raise Exception(str(e))  
        except requests.exceptions.RequestException as e:  
            raise Exception(f"Connection error: {str(e)}")  
      
    # ================================================================  
    # AUTHENTICATION & USER MANAGEMENT  
    # ================================================================  
      
    def login(self, username: str, password: str) -> Dict:  
        """  
        Login with username and password  
          
        Returns:  
            dict: User data or MFA requirement  
        """  
        data = {  
            "username": username,  
            "password": password  
        }  
        result = self._request("POST", "/users/auth/login", json=data)  
          
        if not result.get('mfa_required'):  
            self.current_user = result.get('user')  
          
        return result  
      
    def send_mfa_code(self, username: str, email: str) -> Dict:  
        """Send MFA code to email"""  
        data = {  
            "username": username,  
            "email": email  
        }  
        return self._request("POST", "/users/auth/mfa/send", json=data)  
      
    def verify_mfa_code(self, username: str, code: str) -> Dict:  
        """Verify MFA code and complete login"""  
        data = {  
            "username": username,  
            "code": code  
        }  
        result = self._request("POST", "/users/auth/mfa/verify", json=data)  
        self.current_user = result.get('user')  
        return result  
      
    def logout(self):  
        """Clear current user session"""  
        self.current_user = None  
        self.auth_token = None  
      
    # ================================================================  
    # USER MANAGEMENT  
    # ================================================================  
      
    def get_users(self, role: Optional[str] = None) -> List[Dict]:  
        """  
        Get all users  
          
        Args:  
            role: Optional role filter (admin, manager, staff, retailer)  
        """  
        params = {'role': role} if role else {}  
        result = self._request("GET", "/users", params=params)  
        return result.get('users', [])  
      
    def get_user(self, user_id: int, include_image: bool = False) -> Dict:  
        """Get single user by ID"""  
        params = {'include_image': 'true'} if include_image else {}  
        return self._request("GET", f"/users/{user_id}", params=params)  
      
    def create_user(self, username: str, password: str, full_name: str,   
                   email: str, role: str = "staff", user_image: Optional[bytes] = None) -> Dict:  
        """Create new user"""  
        data = {  
            "username": username,  
            "password": password,  
            "full_name": full_name,  
            "email": email,  
            "role": role  
        }  
          
        if user_image:
            data['image_data'] = user_image
          
        return self._request("POST", "/users", json=data)  
      
    def update_user(self, user_id: int, **kwargs) -> Dict:  
        """Update user (partial)"""  
        return self._request("PATCH", f"/users/{user_id}", json=kwargs)  
      
    def delete_user(self, user_id: int) -> Dict:  
        """Delete user"""  
        return self._request("DELETE", f"/users/{user_id}")  
      
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict:  
        """Change user password"""  
        data = {  
            "old_password": old_password,  
            "new_password": new_password  
        }  
        return self._request("POST", f"/users/{user_id}/change-password", json=data)  
      
    # ================================================================  
    # CATEGORY MANAGEMENT  
    # ================================================================  
      
    def get_categories(self, include_image: bool = False) -> List[Dict]:  
        """Get all categories"""  
        params = {'include_image': 'true'} if include_image else {}  
        result = self._request("GET", "/categories", params=params)  
        return result.get('categories', [])  
      
    def get_category(self, category_id: int, include_image: bool = False) -> Dict:  
        """Get single category"""  
        params = {'include_image': 'true'} if include_image else {}  
        return self._request("GET", f"/categories/{category_id}", params=params)  
      
    def create_category(self, name: str, description: Optional[str] = None,   
                       category_image: Optional[bytes] = None) -> Dict:  
        """Create new category"""  
        data = {  
            "name": name,  
            "description": description  
        }  
          
        if category_image:
            data['image_data'] = category_image
          
        return self._request("POST", "/categories", json=data)  
      
    def update_category(self, category_id: int, **kwargs) -> Dict:  
        """Update category (partial)"""  
        return self._request("PATCH", f"/categories/{category_id}", json=kwargs)  
      
    def delete_category(self, category_id: int) -> Dict:  
        """Delete category"""  
        return self._request("DELETE", f"/categories/{category_id}")  
      
    # ================================================================  
    # PRODUCT MANAGEMENT  
    # ================================================================  
      
    def get_products(self, page: int = 1, per_page: int = 10,   
                    include_image: bool = False, **filters) -> Dict:  
        """  
        Get products with filtering and pagination  
          
        Args:  
            page: Page number  
            per_page: Items per page  
            include_image: Include product images  
            **filters: name, brand, category_id, price_gt, price_gte, price_lt, price_lte  
        """  
        params = {  
            'page': page,  
            'per_page': per_page,  
            'include_image': 'true' if include_image else 'false',  
            **filters  
        }  
        return self._request("GET", "/products", params=params)  
      
    def get_product(self, product_id: int, include_image: bool = False,   
                   include_batches: bool = False) -> Dict:  
        """Get single product"""  
        params = {  
            'include_image': 'true' if include_image else 'false',  
            'include_batches': 'true' if include_batches else 'false'  
        }  
        return self._request("GET", f"/products/{product_id}", params=params)  
      
    def create_product(self, name: str, price: int, brand: Optional[str] = None,  
                      category_id: Optional[int] = None, min_stock_level: int = 10,  
                      details: Optional[str] = None, product_image: Optional[bytes] = None,  
                      stock_level: Optional[int] = None, expiration_date: Optional[str] = None,  
                      added_by: Optional[int] = None) -> Dict:  
        """Create new product"""  
        data = {  
            "name": name,  
            "price": price,  
            "brand": brand,  
            "category_id": category_id,  
            "min_stock_level": min_stock_level,  
            "details": details,  
            "stock_level": stock_level,  
            "expiration_date": expiration_date,  
            "added_by": added_by or (self.current_user['id'] if self.current_user else None)  
        }  
          
        # Remove None values  
        data = {k: v for k, v in data.items() if v is not None}  
          
        if product_image:
            data['image_data'] = product_image
          
        return self._request("POST", "/products", json=data)  
      
    def update_product(self, product_id: int, **kwargs) -> Dict:  
        """Update product (partial)"""  
        if self.current_user and 'added_by' not in kwargs:  
            kwargs['added_by'] = self.current_user['id']  
        return self._request("PATCH", f"/products/{product_id}", json=kwargs)  
      
    def delete_product(self, product_id: int, user_id: Optional[int] = None) -> Dict:  
        """Delete product"""  
        data = {  
            "user_id": user_id or (self.current_user['id'] if self.current_user else None)  
        }  
        return self._request("DELETE", f"/products/{product_id}", json=data)  
      
    # ================================================================  
    # STOCK BATCH MANAGEMENT  
    # ================================================================  
      
    def get_stock_batches(self, product_id: int) -> Dict:  
        """Get all stock batches for a product"""  
        return self._request("GET", f"/products/{product_id}/stock_batches")  
      
    def add_stock_batch(self, product_id: int, quantity: int,   
                       expiration_date: str, reason: str = "Stock added",  
                       added_by: Optional[int] = None) -> Dict:  
        """Add new stock batch"""  
        data = {  
            "quantity": quantity,  
            "expiration_date": expiration_date,  
            "reason": reason,  
            "added_by": added_by or (self.current_user['id'] if self.current_user else None)  
        }  
        return self._request("POST", f"/products/{product_id}/stock_batches", json=data)  
      
    def dispose_product(self, product_id: int, quantity: int, reason: str,  
                       user_id: Optional[int] = None) -> Dict:  
        """Dispose product stock using FEFO"""  
        data = {  
            "quantity": quantity,  
            "reason": reason,  
            "user_id": user_id or (self.current_user['id'] if self.current_user else None)  
        }  
        return self._request("POST", f"/log/dispose", json=data)  
      
    def delete_stock_batch(self, product_id: int, batch_id: int,  
                          user_id: Optional[int] = None) -> Dict:  
        """Delete stock batch"""  
        data = {  
            "user_id": user_id or (self.current_user['id'] if self.current_user else None)  
        }  
        return self._request("DELETE", f"/products/{product_id}/stock_batches/{batch_id}", json=data)  
      
    # ================================================================  
    # SALES MANAGEMENT  
    # ================================================================  
      
    def record_sale(self, retailer_id: int, items: List[Dict],   
                   total_amount: float) -> Dict:  
        """  
        Record a new sale  
          
        Args:  
            retailer_id: ID of the retailer  
            items: List of dicts with product_id, quantity, line_total  
            total_amount: Total sale amount  
              
        Example:  
            items = [  
                {"product_id": 1, "quantity": 2, "line_total": 100.00},  
                {"product_id": 2, "quantity": 1, "line_total": 50.00}  
            ]  
        """  
        data = {  
            "retailer_id": retailer_id,  
            "items": items,  
            "total_amount": total_amount  
        }  
        return self._request("POST", "/sales", json=data)  
      
    def get_sales(self, start_date: Optional[str] = None,   
                 end_date: Optional[str] = None,  
                 retailer_id: Optional[int] = None) -> Dict:  
        """Get sales with optional filtering"""  
        params = {}  
        if start_date:  
            params['start_date'] = start_date  
        if end_date:  
            params['end_date'] = end_date  
        if retailer_id:  
            params['retailer_id'] = retailer_id  
          
        return self._request("GET", "/sales/reports", params=params)  
      
    def get_sale(self, sale_id: int, include_items: bool = True) -> Dict:  
        """Get single sale"""  
        params = {'include_items': 'true' if include_items else 'false'}  
        return self._request("GET", f"/sales/{sale_id}", params=params)  
      
    def undo_sale(self, sale_id: int, user_id: Optional[int] = None) -> Dict:  
        """Undo a sale (admin only)"""  
        data = {  
            "user_id": user_id or (self.current_user['id'] if self.current_user else None)  
        }  
        return self._request("DELETE", f"/sales/{sale_id}", json=data)  
      
    # ================================================================  
    # LOGS & AUDIT  
    # ================================================================  
      
    def get_product_logs(self, product_id: int, limit: int = 50) -> Dict:  
        """Get logs for a specific product"""  
        params = {'limit': limit}  
        return self._request("GET", f"/log/product/{product_id}", params=params)  
      
    def get_user_logs(self, user_id: int, limit: int = 50) -> Dict:  
        """Get logs for a specific user"""  
        params = {'limit': limit}  
        return self._request("GET", f"/log/user/{user_id}", params=params)  
      
    def get_all_logs(self, action_type: Optional[str] = None, limit: int = 100) -> Dict:  
        """Get all product logs"""  
        params = {'limit': limit}  
        if action_type:  
            params['action_type'] = action_type  
        return self._request("GET", "/log", params=params)  
      
    def get_disposal_report(self, start_date: Optional[str] = None,  
                           end_date: Optional[str] = None, limit: int = 100) -> Dict:  
        """Get disposal report"""  
        params = {'limit': limit}  
        if start_date:  
            params['start_date'] = start_date  
        if end_date:  
            params['end_date'] = end_date  
        return self._request("GET", "/log/disposal", params=params)  
      
    def get_api_logs(self, method: Optional[str] = None,   
                    target_entity: Optional[str] = None, limit: int = 100) -> Dict:  
        """Get API activity logs"""  
        params = {'limit': limit}  
        if method:  
            params['method'] = method  
        if target_entity:  
            params['target_entity'] = target_entity  
        return self._request("GET", "/log/api", params=params)  
      
    # ================================================================  
    # METRICS & PERFORMANCE  
    # ================================================================  
      
    def get_retailer_metrics(self, user_id: int) -> Dict:  
        """Get metrics for a specific retailer"""  
        return self._request("GET", f"/retailer/{user_id}")  
      
    def get_leaderboard(self, limit: int = 10) -> Dict:  
        """Get retailer leaderboard"""  
        params = {'limit': limit}  
        return self._request("GET", "/retailer/leaderboard", params=params)  
      
    def get_all_metrics(self) -> Dict:  
        """Get all retailer metrics"""  
        return self._request("GET", "/metrics/all")  
      
    def update_retailer_quota(self, user_id: int, new_quota: float,  
                             updated_by: Optional[int] = None) -> Dict:  
        """Update retailer's daily quota"""  
        data = {  
            "new_quota": new_quota,  
            "updated_by": updated_by or (self.current_user['id'] if self.current_user else None)  
        }  
        return self._request("PATCH", f"/metrics/retailer/{user_id}/quota", json=data)  
      
    # ================================================================  
    # REPORTS  
    # ================================================================  
      
    def get_sales_performance_report(self, start_date: Optional[str] = None,  
                                    end_date: Optional[str] = None) -> Dict:  
        """Get sales performance report"""  
        params = {}  
        if start_date:  
            params['start_date'] = start_date  
        if end_date:  
            params['end_date'] = end_date  
        return self._request("GET", "/reports/sales-performance", params=params)  
      
    def get_detailed_transaction_report(self, start_date: Optional[str] = None,  
                                       end_date: Optional[str] = None) -> Dict:  
        """Get detailed sales transaction report"""  
        params = {}  
        if start_date:  
            params['start_date'] = start_date  
        if end_date:  
            params['end_date'] = end_date  
        return self._request('GET', 'reports/transactions', params=params)
    
    def get_user_accounts_report(self) -> tuple:
        """Report 7: User Accounts Report"""
        return self._request('GET', 'reports/user-accounts')
    
    # PDF Downloads
    def download_pdf_report(self, report_type: str, **params) -> bytes:
        """
        Download PDF report
        
        Args:
            report_type: One of 'sales-performance', 'category-distribution',
                        'retailer-performance', 'alerts', 'managerial-activity',
                        'transactions', 'user-accounts'
            **params: Query parameters for the report (dates, filters, etc.)
        
        Returns:
            bytes: PDF file content
        """
        url = self._url(f'reports/{report_type}/pdf')
        response = requests.get(url, params=params, timeout=self.timeout)
        
        if response.status_code != 200:
            raise StockaDoodleAPIError(f"Failed to download PDF: {response.status_code}")
        
        return response.content
    
    # ==================================================================
    # NOTIFICATIONS ENDPOINTS
    # ==================================================================
    
    def send_low_stock_alerts(self, triggered_by: int = None) -> tuple:
        """Send low stock alerts to managers"""
        return self._request('POST', 'notifications/low-stock',
                           json={'triggered_by': triggered_by})
    
    def send_expiration_alerts(self, days_ahead: int = 7, 
                              triggered_by: int = None) -> tuple:
        """Send expiration alerts to managers"""
        data = {'days_ahead': days_ahead, 'triggered_by': triggered_by}
        return self._request('POST', 'notifications/expiring', json=data)
    
    def send_daily_summary(self, triggered_by: int = None) -> tuple:
        """Send daily inventory summary to managers"""
        return self._request('POST', 'notifications/daily-summary',
                           json={'triggered_by': triggered_by})
    
    def get_notification_history(self, limit: int = 50, 
                                 notification_type: str = None) -> tuple:
        """Get notification history"""
        params = {'limit': limit, 'notification_type': notification_type}
        return self._request('GET', 'notifications/history', params=params)
    
    # ==================================================================
    # HEALTH CHECK
    # ==================================================================
    
    def health_check(self) -> tuple:
        """Check API server health"""
        return self._request('GET', 'health')