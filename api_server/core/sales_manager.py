# api_server/core/sales_manager.py

from extensions import db
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
        
        Args:
            retailer_id (int): ID of the retailer making the sale
            items (list): List of dicts with 'product_id', 'quantity', 'line_total'
                         Example: [{"product_id": 1, "quantity": 3, "line_total": 150}, ...]
            total_amount (float): Total sale amount
            
        Returns:
            Sale: The created sale object
            
        Raises:
            SalesError: If sale cannot be completed
            InventoryError: If insufficient stock
        """
        try:
            # Phase 1: Validate all items first (prevents partial deductions)
            for item in items:
                product = Product.query.get(item['product_id'])
                if not product:
                    raise SalesError(f"Product ID {item['product_id']} not found")
                
                InventoryManager.validate_stock(item['product_id'], item['quantity'])

            # Phase 2: Deduct stock using FEFO
            for item in items:
                InventoryManager.deduct_stock_fefo(
                    product_id=item['product_id'],
                    qty_needed=item['quantity'],
                    user_id=retailer_id,
                    reason="Sale"
                )

            # Phase 3: Create sale record
            sale = Sale(
                retailer_id=retailer_id,
                total_amount=total_amount,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(sale)
            db.session.flush()  # Get sale ID

            # Phase 4: Create sale items
            for item in items:
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    line_total=item['line_total']
                )
                db.session.add(sale_item)

            # Phase 5: Update retailer metrics
            SalesManager._update_retailer_metrics(retailer_id, total_amount)

            # Phase 6: Log the transaction
            product_names = [Product.query.get(item['product_id']).name for item in items]
            ActivityLogger.log_api_activity(
                method='POST',
                target_entity='sale',
                user_id=retailer_id,
                details=f"Sale ID {sale.id}: {len(items)} items ({', '.join(product_names)}), total ${total_amount:.2f}"
            )

            db.session.commit()
            return sale

        except (InventoryError, SalesError) as e:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise SalesError(f"Failed to complete sale: {str(e)}")

    @staticmethod
    def _update_retailer_metrics(retailer_id, sale_amount):
        """
        Update retailer performance metrics after a sale.
        Handles streaks, quotas, and totals.
        
        Args:
            retailer_id (int): Retailer ID
            sale_amount (float): Amount of the sale
        """
        metrics = RetailerMetrics.query.filter_by(retailer_id=retailer_id).first()
        
        if not metrics:
            # Create new metrics record
            metrics = RetailerMetrics(
                retailer_id=retailer_id,
                daily_quota=500.0,  # Default quota
                sales_today=0.0,
                total_sales=0.0,
                total_transactions=0
            )
            db.session.add(metrics)

        today = date.today()
        
        # Reset daily sales if it's a new day
        if metrics.last_sale_date and metrics.last_sale_date < today:
            # Check if streak should continue
            yesterday = today - timedelta(days=1)
            if metrics.last_sale_date == yesterday and metrics.sales_today >= metrics.daily_quota:
                metrics.current_streak += 1
            else:
                metrics.current_streak = 0
            
            metrics.sales_today = 0.0

        # Update metrics
        metrics.sales_today += sale_amount
        metrics.total_sales += sale_amount
        metrics.total_transactions += 1
        metrics.last_sale_date = today

        # Check if quota met today (for streak tracking)
        if metrics.sales_today >= metrics.daily_quota and metrics.current_streak == 0:
            metrics.current_streak = 1

    @staticmethod
    def undo_sale(sale_id, user_id):
        """
        Reverse a sale transaction (restore stock, adjust metrics).
        
        Args:
            sale_id (int): Sale to undo
            user_id (int): User performing the undo
            
        Returns:
            bool: True if successful
            
        Raises:
            SalesError: If sale not found or cannot be undone
        """
        sale = Sale.query.get(sale_id)
        if not sale:
            raise SalesError(f"Sale ID {sale_id} not found")

        try:
            # Restore stock for each item (add back as new batches)
            for item in sale.items:
                InventoryManager.add_stock_batch(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    user_id=user_id
                )

            # Adjust retailer metrics
            metrics = RetailerMetrics.query.filter_by(retailer_id=sale.retailer_id).first()
            if metrics:
                metrics.sales_today = max(0, metrics.sales_today - sale.total_amount)
                metrics.total_sales = max(0, metrics.total_sales - sale.total_amount)
                metrics.total_transactions = max(0, metrics.total_transactions - 1)

            # Log the undo
            ActivityLogger.log_api_activity(
                method='DELETE',
                target_entity='sale',
                user_id=user_id,
                details=f"Undid sale ID {sale_id}, amount ${sale.total_amount:.2f}"
            )

            # Delete sale
            db.session.delete(sale)
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise SalesError(f"Failed to undo sale: {str(e)}")

    @staticmethod
    def get_sale(sale_id):
        """
        Get a specific sale by ID.
        
        Args:
            sale_id (int): Sale ID
            
        Returns:
            Sale: Sale object or None
        """
        return Sale.query.get(sale_id)

    @staticmethod
    def get_sales_report(start_date=None, end_date=None, retailer_id=None):
        """
        Generate a sales report for a date range.
        
        Args:
            start_date (datetime, optional): Start of date range
            end_date (datetime, optional): End of date range
            retailer_id (int, optional): Filter by specific retailer
            
        Returns:
            dict: Report data with sales list and summary
        """
        query = Sale.query
        
        if start_date:
            query = query.filter(Sale.created_at >= start_date)
        if end_date:
            query = query.filter(Sale.created_at <= end_date)
        if retailer_id:
            query = query.filter_by(retailer_id=retailer_id)

        sales = query.order_by(Sale.created_at.desc()).all()
        
        total_revenue = sum(s.total_amount for s in sales)
        total_transactions = len(sales)
        
        # Calculate total items sold
        total_items = sum(
            sum(item.quantity for item in sale.items)
            for sale in sales
        )

        return {
            'sales': [s.to_dict(include_items=True) for s in sales],
            'summary': {
                'total_revenue': round(total_revenue, 2),
                'total_transactions': total_transactions,
                'total_items_sold': total_items,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'retailer_id': retailer_id
            }
        }

    @staticmethod
    def get_retailer_performance(retailer_id):
        """
        Get performance metrics for a specific retailer.
        
        Args:
            retailer_id (int): Retailer ID
            
        Returns:
            dict: Retailer performance data
        """
        metrics = RetailerMetrics.query.filter_by(retailer_id=retailer_id).first()
        
        if not metrics:
            return {
                'retailer_id': retailer_id,
                'current_streak': 0,
                'daily_quota': 500.0,
                'sales_today': 0.0,
                'total_sales': 0.0,
                'total_transactions': 0,
                'quota_progress': 0.0
            }

        quota_progress = (metrics.sales_today / metrics.daily_quota * 100) if metrics.daily_quota > 0 else 0

        return {
            'retailer_id': retailer_id,
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
        
        Args:
            limit (int): Number of retailers to return
            
        Returns:
            list: Top retailers with performance data
        """
        from models.user import User
        
        top_metrics = (
            RetailerMetrics.query
            .order_by(
                RetailerMetrics.current_streak.desc(),
                RetailerMetrics.total_sales.desc()
            )
            .limit(limit)
            .all()
        )

        leaderboard = []
        for idx, metrics in enumerate(top_metrics, 1):
            user = User.query.get(metrics.retailer_id)
            leaderboard.append({
                'rank': idx,
                'retailer_id': metrics.retailer_id,
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
        
        Args:
            retailer_id (int): Retailer ID
            new_quota (float): New daily quota amount
            
        Returns:
            RetailerMetrics: Updated metrics
            
        Raises:
            SalesError: If retailer not found or invalid quota
        """
        if new_quota < 0:
            raise SalesError("Quota must be non-negative")
        
        metrics = RetailerMetrics.query.filter_by(retailer_id=retailer_id).first()
        
        if not metrics:
            raise SalesError(f"Retailer ID {retailer_id} not found")
        
        old_quota = metrics.daily_quota
        metrics.daily_quota = new_quota
        db.session.commit()
        
        # Log quota change
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
        
        Returns:
            int: Number of retailers processed
        """
        all_metrics = RetailerMetrics.query.all()
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        updated_count = 0
        
        for metrics in all_metrics:
            if metrics.last_sale_date == yesterday:
                # Check if quota was met yesterday
                if metrics.sales_today >= metrics.daily_quota:
                    metrics.current_streak += 1
                else:
                    metrics.current_streak = 0
            elif metrics.last_sale_date and metrics.last_sale_date < yesterday:
                # Missed days, reset streak
                metrics.current_streak = 0
            
            # Reset daily sales
            metrics.sales_today = 0.0
            updated_count += 1
        
        db.session.commit()
        return updated_count