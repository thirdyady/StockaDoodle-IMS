# api_server/core/activity_logger.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union

from models.product_log import ProductLog
from models.api_activity_log import APIActivityLog
from models.user import User


class ActivityLogger:
    """
    Centralized logging service for all inventory and product-related actions.
    Creates audit trails for accountability and compliance.

    This implementation is intentionally tolerant:
    - Accepts user as:
        * User object
        * int user id
        * None
    - Normalizes to a User object where possible.
    """

    @staticmethod
    def _resolve_user(user_ref: Optional[Union[int, User]]) -> Optional[User]:
        """Convert an int user id or User object into a User object."""
        if user_ref is None:
            return None

        if isinstance(user_ref, User):
            return user_ref

        try:
            return User.objects(id=int(user_ref)).first()
        except Exception:
            return None

    # ---------------------------------------------------------
    # Product-level logs
    # ---------------------------------------------------------
    @staticmethod
    def log_product_action(
        product_id: int,
        user_id: Optional[Union[int, User]],
        action_type: str,
        quantity: Optional[int] = None,
        notes: Optional[str] = None
    ):
        """
        Log a product-related action (restock, dispose, edit, sale, etc.)
        """
        user_obj = ActivityLogger._resolve_user(user_id)

        final_notes = notes
        if quantity is not None:
            if final_notes:
                final_notes = f"Quantity: {quantity}. {final_notes}"
            else:
                final_notes = f"Quantity: {quantity}."

        log = ProductLog(
            product_id=product_id,
            user=user_obj,
            action_type=action_type,
            quantity=quantity,
            notes=final_notes,
            log_time=datetime.now(timezone.utc)
        )
        log.save()
        return log

    # ---------------------------------------------------------
    # API-level logs
    # ---------------------------------------------------------
    @staticmethod
    def log_api_activity(
        method: str,
        target_entity: str,
        user_id: Optional[Union[int, User]] = None,
        source: str = "API",
        details: Optional[str] = None
    ):
        """
        Log API-level activity for broader system auditing.
        """
        user_obj = ActivityLogger._resolve_user(user_id)

        safe_method = (method or "").upper().strip() or "UNKNOWN"
        safe_target = (target_entity or "").strip() or "unknown"

        log = APIActivityLog(
            method=safe_method,
            target_entity=safe_target,
            user=user_obj,
            source=source,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        log.save()
        return log

    # ---------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------
    @staticmethod
    def get_product_logs(product_id, limit=50):
        return (
            ProductLog.objects(product_id=product_id)
            .order_by('-log_time')
            .limit(limit)
        )

    @staticmethod
    def get_user_logs(user_id, limit=50):
        user_obj = ActivityLogger._resolve_user(user_id)
        if not user_obj:
            return ProductLog.objects().none()

        return (
            ProductLog.objects(user=user_obj)
            .order_by('-log_time')
            .limit(limit)
        )

    @staticmethod
    def get_all_logs(limit=100, action_type=None):
        query = ProductLog.objects()
        if action_type:
            query = query.filter(action_type=action_type)
        return query.order_by('-log_time').limit(limit)

    @staticmethod
    def get_api_logs(limit=100, method=None, target_entity=None):
        query = APIActivityLog.objects()
        if method:
            query = query.filter(method=str(method).upper())
        if target_entity:
            query = query.filter(target_entity=target_entity)
        return query.order_by('-timestamp').limit(limit)
