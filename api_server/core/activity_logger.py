from models.product_log import ProductLog
from models.api_activity_log import APIActivityLog
from datetime import datetime, timezone


class ActivityLogger:
    """
    Centralized logging service for all inventory and product-related actions.
    Creates audit trails for accountability and compliance.
    """

    @staticmethod
    def log_product_action(product_id, user_id, action_type, quantity=None, notes=None):
        """
        Log a product-related action (restock, dispose, edit, etc.)
        
        Args:
            product_id (int): ID of the affected product
            user_id (int): ID of the user performing the action
            action_type (str): Type of action (Restock, Dispose, Edit, Sale, etc.)
            notes (str, optional): Additional details about the action
            
        Returns:
            ProductLog: The created log entry
        """
        log = ProductLog(
            product_id=product_id,
            user=user_id,
            action_type=action_type,
            notes=f"Quantity: {quantity}. {notes}" if quantity else notes,
            log_time=datetime.now(timezone.utc)
        )
        log.save()
        return log

    @staticmethod
    def log_api_activity(method, target_entity, user_id=None, source="API", details=None):
        """
        Log API-level activity for broader system auditing.
        
        Args:
            method (str): HTTP method (GET, POST, PATCH, DELETE)
            target_entity (str): Entity being affected (product, user, sale)
            user_id (int, optional): User making the request
            source (str): Source of the request (API, Desktop App, etc.)
            details (str, optional): JSON or text with additional context
            
        Returns:
            APIActivityLog: The created log entry
        """
        log = APIActivityLog(
            method=method,
            target_entity=target_entity,
            user=user_id,
            source=source,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        log.save()
        return log

    @staticmethod
    def get_product_logs(product_id, limit=50):
        """
        Retrieve logs for a specific product.
        
        Args:
            product_id (int): Product to fetch logs for
            limit (int): Maximum number of logs to return
            
        Returns:
            list: List of ProductLog entries
        """
        return (
            ProductLog.objects(product_id=product_id)
            .order_by('-log_time')
            .limit(limit)
        )

    @staticmethod
    def get_user_logs(user_id, limit=50):
        """
        Retrieve logs for actions performed by a specific user.
        
        Args:
            user_id (int): User to fetch logs for
            limit (int): Maximum number of logs to return
            
        Returns:
            list: List of ProductLog entries
        """
        return (
            ProductLog.objects(user=user_id)
            .order_by('-log_time')
            .limit(limit)
        )

    @staticmethod
    def get_all_logs(limit=100, action_type=None):
        """
        Retrieve all product logs with optional filtering.
        
        Args:
            limit (int): Maximum number of logs to return
            action_type (str, optional): Filter by specific action type
            
        Returns:
            list: List of ProductLog entries
        """
        query = ProductLog.objects()
        
        if action_type:
            query = query.filter(action_type=action_type)
            
        return query.order_by('-log_time').limit(limit)

    @staticmethod
    def get_api_logs(limit=100, method=None, target_entity=None):
        """
        Retrieve API activity logs with optional filtering.
        
        Args:
            limit (int): Maximum number of logs to return
            method (str, optional): Filter by HTTP method
            target_entity (str, optional): Filter by entity type
            
        Returns:
            list: List of APIActivityLog entries
        """
        query = APIActivityLog.objects()
        
        if method:
            query = query.filter(method=method)
        if target_entity:
            query = query.filter(target_entity=target_entity)
            
        return query.order_by('-timestamp').limit(limit)