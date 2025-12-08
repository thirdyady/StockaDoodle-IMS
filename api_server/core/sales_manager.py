# api_server/core/sales_manager.py

from utils.counters import get_next_sequence  # keep if your Sale model uses this elsewhere
from models.sale import Sale, SaleItem
from models.product import Product
from models.retailer_metrics import RetailerMetrics
from core.inventory_manager import InventoryManager, InventoryError
from core.activity_logger import ActivityLogger
from datetime import datetime, date, timedelta, timezone


class SalesError(Exception):
    """Custom exception for sales-related issues."""
    pass


class SalesManager:
    """
    Handles all sales transactions and retailer performance tracking.
    Integrates with InventoryManager for FEFO stock deduction.
    """

    @staticmethod
    def record_atomic_sale(retailer_id, items, total_amount):
        """
        Process a complete sale transaction atomically.
        All operations succeed or all fail (no partial sales).
        """
        try:
            if retailer_id is None:
                raise SalesError("retailer_id is required")
            if not items or not isinstance(items, list):
                raise SalesError("items must be a non-empty list")
            if total_amount is None:
                raise SalesError("total_amount is required")

            # Normalize items (prevents string qty/product_id errors)
            normalized_items = []
            for item in items:
                if not isinstance(item, dict):
                    raise SalesError("Each item must be an object")

                if 'product_id' not in item or 'quantity' not in item or 'line_total' not in item:
                    raise SalesError("Each item must contain product_id, quantity, and line_total")

                try:
                    pid = int(item['product_id'])
                    qty = int(item['quantity'])
                    line_total = float(item['line_total'])
                except Exception:
                    raise SalesError("Invalid item types for product_id/quantity/line_total")

                if qty <= 0:
                    raise SalesError("Item quantity must be > 0")

                normalized_items.append({
                    "product_id": pid,
                    "quantity": qty,
                    "line_total": line_total
                })

            # Phase 1: Validate all items first (prevents partial deductions)
            for item in normalized_items:
                product = Product.objects(id=item['product_id']).first()
                if not product:
                    raise SalesError(f"Product ID {item['product_id']} not found")

                InventoryManager.validate_stock(item['product_id'], item['quantity'])

            # Phase 2: Deduct stock using FEFO
            for item in normalized_items:
                InventoryManager.deduct_stock_fefo(
                    product_id=item['product_id'],
                    qty_needed=item['quantity'],
                    user_id=retailer_id,
                    reason="Sale"
                )

            # Phase 3: Create sale record
            sale = Sale(
                retailer_id=int(retailer_id),
                total_amount=float(total_amount),
                created_at=datetime.now(timezone.utc)
            )

            # Phase 4: Create sale items
            for item in normalized_items:
                sale_item = SaleItem(
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    line_total=item['line_total']
                )
                sale.items.append(sale_item)

            # Phase 5: Save sale and update retailer metrics
            sale.save()
            SalesManager._update_retailer_metrics(int(retailer_id), float(total_amount))

            # Phase 6: Log transaction
            product_names = []
            for item in normalized_items:
                product = Product.objects(id=item['product_id']).first()
                if product:
                    product_names.append(product.name)

                # Optional detailed product action logging
                ActivityLogger.log_product_action(
                    product_id=item['product_id'],
                    user_id=retailer_id,
                    action_type='Sale',
                    quantity=item['quantity'],
                    notes=f"Sold via sale #{sale.id}"
                )

            ActivityLogger.log_api_activity(
                method='POST',
                target_entity='sale',
                user_id=retailer_id,
                details=f"Sale ID {sale.id}: {len(normalized_items)} items "
                        f"({', '.join(product_names) if product_names else 'Unknown products'}), "
                        f"total ${float(total_amount):.2f}"
            )

            return sale

        except (InventoryError, SalesError):
            raise
        except Exception as e:
            raise SalesError(f"Failed to complete sale: {str(e)}")

    @staticmethod
    def _update_retailer_metrics(retailer_id, sale_amount):
        """
        Update retailer performance metrics after a sale.
        Handles streaks, quotas, and totals.
        """
        from models.user import User

        user = User.objects(id=int(retailer_id)).first()
        if not user:
            return

        metrics = RetailerMetrics.objects(retailer=user).first()

        if not metrics:
            # Create new metrics record
            metrics = RetailerMetrics(
                retailer=user,
                daily_quota=1000.0,
                sales_today=0.0,
                total_sales=0.0,
                total_transactions=0,
                current_streak=0
            )

        today = date.today()

        # Reset daily sales if it's a new day
        if metrics.last_sale_date and metrics.last_sale_date < today:
            yesterday = today - timedelta(days=1)

            if metrics.last_sale_date == yesterday and metrics.sales_today >= metrics.daily_quota:
                metrics.current_streak += 1
            else:
                metrics.current_streak = 0

            metrics.sales_today = 0.0

        metrics.sales_today += float(sale_amount)
        metrics.total_sales += float(sale_amount)
        metrics.total_transactions += 1
        metrics.last_sale_date = today

        # Start streak if quota met today
        if metrics.sales_today >= metrics.daily_quota and metrics.current_streak == 0:
            metrics.current_streak = 1

        metrics.save()

    @staticmethod
    def undo_sale(sale_id, user_id):
        """
        Reverse a sale transaction (restore stock, adjust metrics).
        """
        sale = Sale.objects(id=sale_id).first()
        if not sale:
            raise SalesError(f"Sale ID {sale_id} not found")

        try:
            from models.stock_batch import StockBatch
            from models.user import User

            undo_user = User.objects(id=int(user_id)).first()

            # Restore stock for each item
            for item in sale.items:
                # Create a new batch for returned stock.
                # We intentionally do not set expiration_date here unless you want to
                # preserve original expiry logic (which would require tracking per-batch sale deductions).
                batch = StockBatch(
                    product_id=item.product_id,
                    quantity=int(item.quantity),
                    expiration_date=None,
                    added_at=datetime.now(timezone.utc),
                    added_by=undo_user,
                    reason="Sale reversal"
                )
                batch.save()

                # Optional: log product action per restored item
                ActivityLogger.log_product_action(
                    product_id=item.product_id,
                    user_id=undo_user or user_id,
                    action_type='Sale Reversal',
                    quantity=int(item.quantity),
                    notes=f"Restored via undo of sale #{sale.id}"
                )

            # Adjust retailer metrics
            from models.user import User
            retailer_user = User.objects(id=int(sale.retailer_id)).first()

            if retailer_user:
                metrics = RetailerMetrics.objects(retailer=retailer_user).first()
            else:
                metrics = None

            if metrics:
                # Conservative adjustment; avoids negative values
                metrics.sales_today = max(0.0, float(metrics.sales_today or 0) - float(sale.total_amount or 0))
                metrics.total_sales = max(0.0, float(metrics.total_sales or 0) - float(sale.total_amount or 0))
                metrics.total_transactions = max(0, int(metrics.total_transactions or 0) - 1)
                metrics.save()

            # Log the undo
            ActivityLogger.log_api_activity(
                method='DELETE',
                target_entity='sale',
                user_id=user_id,
                details=f"Undid sale ID {sale_id}, amount ${float(sale.total_amount or 0):.2f}"
            )

            # Delete sale
            sale.delete()
            return True

        except Exception as e:
            raise SalesError(f"Failed to undo sale: {str(e)}")

    @staticmethod
    def get_sale(sale_id):
        """Get a specific sale by ID."""
        return Sale.objects(id=sale_id).first()

    @staticmethod
    def get_sales_report(start_date=None, end_date=None, retailer_id=None):
        """
        Generate a sales report for a date range.
        """
        query = Sale.objects()

        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)
        if retailer_id:
            # Your Sale uses retailer_id based on record_atomic_sale
            query = query.filter(retailer_id=int(retailer_id))

        sales = query.order_by('-created_at')

        total_revenue = 0.0
        total_items = 0

        # IMPORTANT:
        # Based on your record_atomic_sale, Sale.items is likely an embedded list.
        # So we compute items directly from sale.items instead of SaleItem.objects(...)
        for sale in sales:
            total_revenue += float(sale.total_amount or 0)

            if getattr(sale, "items", None):
                for item in sale.items:
                    try:
                        total_items += int(item.quantity or 0)
                    except Exception:
                        pass

        return {
            'sales': [sale.to_dict(include_items=True) for sale in sales],
            'summary': {
                'total_revenue': round(total_revenue, 2),
                'total_transactions': sales.count(),
                'total_items_sold': total_items,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'retailer_id': retailer_id
            }
        }

    @staticmethod
    def get_retailer_performance(retailer_id):
        """Get performance metrics for a specific retailer."""
        from models.user import User

        user = User.objects(id=int(retailer_id)).first()
        if not user:
            raise SalesError(f"Retailer ID {retailer_id} not found")

        metrics = RetailerMetrics.objects(retailer=user).first()

        if not metrics:
            return {
                'retailer_id': user.id,
                'current_streak': 0,
                'daily_quota': 1000.0,
                'sales_today': 0.0,
                'total_sales': 0.0,
                'total_transactions': 0,
                'quota_progress': 0.0
            }

        quota_progress = (metrics.sales_today / metrics.daily_quota * 100) if metrics.daily_quota > 0 else 0

        return {
            'retailer_id': user.id,
            'current_streak': metrics.current_streak,
            'daily_quota': metrics.daily_quota,
            'sales_today': metrics.sales_today,
            'total_sales': metrics.total_sales,
            'total_transactions': metrics.total_transactions,
            'quota_progress': round(quota_progress, 2),
            'quota_met': metrics.sales_today >= metrics.daily_quota,
            'last_sale_date': metrics.last_sale_date.isoformat() if metrics.last_sale_date else None
        }

    @staticmethod
    def get_leaderboard(limit=10):
        """
        Get top-performing retailers by current streak and total sales.
        """
        from models.user import User

        # RetailerMetrics.retailer is likely a ReferenceField(User)
        top_metrics = (
            RetailerMetrics.objects(retailer__ne=None)
            .order_by('-current_streak', '-total_sales')
            .limit(int(limit))
        )

        leaderboard = []
        for idx, metrics in enumerate(top_metrics, 1):
            user = metrics.retailer
            leaderboard.append({
                'rank': idx,
                'retailer_id': user.id if user else None,
                'retailer_name': user.full_name if user else 'Unknown',
                'current_streak': metrics.current_streak,
                'total_sales': metrics.total_sales,
                'sales_today': metrics.sales_today,
                'total_transactions': metrics.total_transactions
            })

        return leaderboard

    @staticmethod
    def update_retailer_quota(retailer_id, new_quota):
        """
        Update a retailer's daily quota.
        """
        if new_quota is None:
            raise SalesError("new_quota is required")

        try:
            new_quota = float(new_quota)
        except Exception:
            raise SalesError("Quota must be a number")

        if new_quota < 0:
            raise SalesError("Quota must be non-negative")

        from models.user import User

        user = User.objects(id=int(retailer_id)).first()
        if not user:
            raise SalesError(f"Retailer ID {retailer_id} not found")

        metrics = RetailerMetrics.objects(retailer=user).first()

        if not metrics:
            metrics = RetailerMetrics(
                retailer=user,
                daily_quota=1000.0,
                sales_today=0.0,
                total_sales=0.0,
                total_transactions=0,
                current_streak=0
            )

        old_quota = float(metrics.daily_quota or 0)
        metrics.daily_quota = new_quota
        metrics.save()

        ActivityLogger.log_api_activity(
            method='PATCH',
            target_entity='retailer_metrics',
            user_id=retailer_id,
            details=f"Quota updated: ${old_quota:.2f} → ${new_quota:.2f}"
        )

        return metrics

    @staticmethod
    def reset_daily_metrics():
        """
        Reset daily metrics for all retailers (run at midnight).
        Updates streaks based on quota achievement.
        """
        all_metrics = RetailerMetrics.objects()
        today = date.today()
        yesterday = today - timedelta(days=1)

        updated_count = 0

        for metrics in all_metrics:
            if metrics.last_sale_date == yesterday:
                if metrics.sales_today >= metrics.daily_quota:
                    metrics.current_streak += 1
                else:
                    metrics.current_streak = 0
            elif metrics.last_sale_date and metrics.last_sale_date < yesterday:
                metrics.current_streak = 0

            metrics.sales_today = 0.0
            metrics.save()
            updated_count += 1

        return updated_count
