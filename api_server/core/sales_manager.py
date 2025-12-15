# api_server/core/sales_manager.py

from utils.counters import get_next_sequence  # keep if used elsewhere
from models.sale import Sale, SaleItem, SaleBatchDeduction
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

    ✅ Now records batch-level FEFO deductions into each SaleItem so that:
      - return_sale_item restores to the ORIGINAL batch (keeps expiry)
      - undo_sale restores to the ORIGINAL batch (keeps expiry)
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

                if "product_id" not in item or "quantity" not in item or "line_total" not in item:
                    raise SalesError("Each item must contain product_id, quantity, and line_total")

                try:
                    pid = int(item["product_id"])
                    qty = int(item["quantity"])
                    line_total = float(item["line_total"])
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
                product = Product.objects(id=int(item["product_id"])).first()
                if not product:
                    raise SalesError(f"Product ID {item['product_id']} not found")

                InventoryManager.validate_stock(int(item["product_id"]), int(item["quantity"]))

            # Phase 2: Deduct stock using FEFO + track exactly which batches were used
            batch_tracking = {}  # product_id -> list of {"batch_id": int, "quantity": int}
            for item in normalized_items:
                deductions = InventoryManager.deduct_stock_fefo(
                    product_id=int(item["product_id"]),
                    qty_needed=int(item["quantity"]),
                    user_id=int(retailer_id),
                    reason="Sale"
                )
                batch_tracking[int(item["product_id"])] = deductions or []

            # Phase 3: Create sale record
            sale = Sale(
                retailer_id=int(retailer_id),
                total_amount=float(total_amount),
                created_at=datetime.now(timezone.utc)
            )

            # Phase 4: Create sale items + persist batch provenance
            for item in normalized_items:
                pid = int(item["product_id"])
                deductions = batch_tracking.get(pid, []) or []

                sale_item = SaleItem(
                    product_id=pid,
                    quantity=int(item["quantity"]),
                    line_total=float(item["line_total"]),
                    batch_deductions=[
                        SaleBatchDeduction(
                            batch_id=int(d.get("batch_id")),
                            quantity=int(d.get("quantity", 0))
                        )
                        for d in deductions
                        if d and d.get("batch_id") is not None
                    ]
                )
                sale.items.append(sale_item)

            # Phase 5: Save sale and update retailer metrics
            sale.save()
            SalesManager._update_retailer_metrics(int(retailer_id), float(total_amount))

            # Phase 6: Log transaction (single place)
            product_names = []
            for item in normalized_items:
                product = Product.objects(id=int(item["product_id"])).first()
                if product:
                    product_names.append(product.name)

                ActivityLogger.log_product_action(
                    product_id=int(item["product_id"]),
                    user_id=int(retailer_id),
                    action_type="Sale",
                    quantity=int(item["quantity"]),
                    notes=f"Sold via sale #{sale.id}"
                )

            ActivityLogger.log_api_activity(
                method="POST",
                target_entity="sale",
                user_id=int(retailer_id),
                details=(
                    f"Sale ID {sale.id}: {len(normalized_items)} items "
                    f"({', '.join(product_names) if product_names else 'Unknown products'}), "
                    f"total ${float(total_amount):.2f}"
                )
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

        ✅ Restores stock back to the ORIGINAL batches that were deducted (keeps expiry).
        """
        sale = Sale.objects(id=int(sale_id)).first()
        if not sale:
            raise SalesError(f"Sale ID {sale_id} not found")

        try:
            from models.stock_batch import StockBatch
            from models.user import User

            # Restore stock for each item back to original batches
            for item in (sale.items or []):
                deductions = list(item.batch_deductions or [])

                # Legacy fallback: if no deductions exist (old data), create a batch like before
                if not deductions:
                    undo_user = User.objects(id=int(user_id)).first()
                    legacy_batch = StockBatch(
                        product_id=int(item.product_id),
                        quantity=int(item.quantity),
                        expiration_date=None,
                        added_at=datetime.now(timezone.utc),
                        added_by=undo_user,
                        reason="Sale reversal (legacy)"
                    )
                    legacy_batch.save()

                    ActivityLogger.log_product_action(
                        product_id=int(item.product_id),
                        user_id=int(user_id),
                        action_type="Sale Reversal",
                        quantity=int(item.quantity),
                        notes=f"Legacy restore via undo of sale #{sale.id} (new batch {legacy_batch.id})"
                    )
                    continue

                for d in deductions:
                    batch = StockBatch.objects(id=int(d.batch_id)).first()
                    if not batch:
                        raise SalesError(f"Original batch {d.batch_id} not found")

                    batch.quantity = int(batch.quantity or 0) + int(d.quantity or 0)
                    batch.save()

                    ActivityLogger.log_product_action(
                        product_id=int(item.product_id),
                        user_id=int(user_id),
                        action_type="Sale Reversal",
                        quantity=int(d.quantity or 0),
                        notes=f"Restored to batch {batch.id} via undo of sale #{sale.id}"
                    )

            # Adjust retailer metrics
            retailer_user = User.objects(id=int(sale.retailer_id)).first()
            metrics = RetailerMetrics.objects(retailer=retailer_user).first() if retailer_user else None

            if metrics:
                metrics.sales_today = max(0.0, float(metrics.sales_today or 0) - float(sale.total_amount or 0))
                metrics.total_sales = max(0.0, float(metrics.total_sales or 0) - float(sale.total_amount or 0))
                metrics.total_transactions = max(0, int(metrics.total_transactions or 0) - 1)
                metrics.save()

            ActivityLogger.log_api_activity(
                method="DELETE",
                target_entity="sale",
                user_id=int(user_id),
                details=f"Undid sale ID {sale_id}, amount ${float(sale.total_amount or 0):.2f}"
            )

            sale.delete()
            return True

        except SalesError:
            raise
        except Exception as e:
            raise SalesError(f"Failed to undo sale: {str(e)}")

    # ------------------------------------------------------------------
    # ✅ Return ONE sale item row (sale_id + item_index)
    # ------------------------------------------------------------------
    @staticmethod
    def return_sale_item(sale_id: int, item_index: int, user_id: int):
        """
        Return ONE sold item line inside a Sale:
        - restores stock for that line back to ORIGINAL batches (keeps expiry)
        - removes that one SaleItem from sale.items
        - recomputes sale.total_amount
        - adjusts retailer metrics (amounts only; transactions only if sale becomes empty)
        """
        sale = Sale.objects(id=int(sale_id)).first()
        if not sale:
            raise SalesError(f"Sale ID {sale_id} not found")

        items = list(sale.items or [])
        if item_index < 0 or item_index >= len(items):
            raise SalesError("Invalid item index")

        try:
            from models.stock_batch import StockBatch
            from models.user import User

            acting_user = User.objects(id=int(user_id)).first()

            target_item = items[item_index]
            product_id = int(target_item.product_id)
            qty = int(target_item.quantity or 0)
            line_total = float(target_item.line_total or 0.0)

            if qty <= 0:
                raise SalesError("Cannot return an item with zero quantity")

            deductions = list(target_item.batch_deductions or [])

            # Legacy fallback if this is older data without batch tracking
            if not deductions:
                legacy_batch = StockBatch(
                    product_id=product_id,
                    quantity=qty,
                    expiration_date=None,
                    added_at=datetime.now(timezone.utc),
                    added_by=acting_user,
                    reason="Returned item (legacy)"
                )
                legacy_batch.save()

                ActivityLogger.log_product_action(
                    product_id=product_id,
                    user_id=int(user_id),
                    action_type="Return",
                    quantity=qty,
                    notes=f"Legacy return from sale #{sale.id} (new batch {legacy_batch.id})"
                )
            else:
                # ✅ Restore stock to original batches
                restored_total = 0
                for d in deductions:
                    batch = StockBatch.objects(id=int(d.batch_id)).first()
                    if not batch:
                        raise SalesError(f"Original batch {d.batch_id} not found")

                    add_qty = int(d.quantity or 0)
                    batch.quantity = int(batch.quantity or 0) + add_qty
                    batch.save()
                    restored_total += add_qty

                    ActivityLogger.log_product_action(
                        product_id=product_id,
                        user_id=int(user_id),
                        action_type="Return",
                        quantity=add_qty,
                        notes=f"Returned to batch {batch.id} from sale #{sale.id} (item index {item_index})"
                    )

                # Safety: if data mismatch, still allow but log it
                if restored_total != qty:
                    ActivityLogger.log_api_activity(
                        method="WARN",
                        target_entity="sale_item_return",
                        user_id=int(user_id),
                        details=(
                            f"Return qty mismatch for sale {sale_id} item {item_index}: "
                            f"item.qty={qty} restored_total={restored_total}"
                        )
                    )

            # 2) Remove item
            del sale.items[item_index]

            # 3) Recompute total
            new_total = 0.0
            for it in (sale.items or []):
                try:
                    new_total += float(it.line_total or 0)
                except Exception:
                    pass
            sale.total_amount = round(new_total, 2)

            # 4) Adjust metrics
            retailer_id = int(sale.retailer_id)

            sale_date = None
            try:
                sale_date = sale.created_at.date() if sale.created_at else None
            except Exception:
                sale_date = None

            retailer_user = User.objects(id=retailer_id).first()
            metrics = RetailerMetrics.objects(retailer=retailer_user).first() if retailer_user else None

            if metrics:
                metrics.total_sales = max(0.0, float(metrics.total_sales or 0) - line_total)

                if sale_date == date.today():
                    metrics.sales_today = max(0.0, float(metrics.sales_today or 0) - line_total)

                if not (sale.items or []):
                    metrics.total_transactions = max(0, int(metrics.total_transactions or 0) - 1)

                metrics.save()

            # 5) If no items left, delete sale. Else save updated sale.
            if not (sale.items or []):
                ActivityLogger.log_api_activity(
                    method="DELETE",
                    target_entity="sale_item",
                    user_id=int(user_id),
                    details=f"Returned last item from sale ID {sale_id}. Sale removed."
                )
                sale.delete()
                return {"deleted_sale": True, "sale_id": int(sale_id)}

            sale.save()

            ActivityLogger.log_api_activity(
                method="DELETE",
                target_entity="sale_item",
                user_id=int(user_id),
                details=f"Returned item index {item_index} from sale ID {sale_id}."
            )

            return {"deleted_sale": False, "sale": sale.to_dict(include_items=True)}

        except SalesError:
            raise
        except Exception as e:
            raise SalesError(f"Failed to return item: {str(e)}")

    @staticmethod
    def get_sale(sale_id):
        """Get a specific sale by ID."""
        return Sale.objects(id=int(sale_id)).first()

    @staticmethod
    def get_sales_report(start_date=None, end_date=None, retailer_id=None):
        """
        Generate a sales report for a date range.

        ✅ Returns BOTH:
          - "sales": legacy sale objects
          - "sale_items": flattened rows (one row per sold item) used by Sales tab
        """
        from models.user import User

        query = Sale.objects()

        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)
        if retailer_id is not None:
            query = query.filter(retailer_id=int(retailer_id))

        sales = query.order_by("-created_at")

        total_revenue = 0.0
        total_items = 0
        sale_items_rows = []

        user_cache = {}
        product_cache = {}

        for sale in sales:
            total_revenue += float(sale.total_amount or 0)

            rid = int(sale.retailer_id)
            if rid not in user_cache:
                u = User.objects(id=rid).first()
                user_cache[rid] = u.full_name if u else "Unknown"
            retailer_name = user_cache.get(rid, "Unknown")

            created_at = sale.created_at.isoformat() if sale.created_at else None

            for idx, item in enumerate(sale.items or []):
                try:
                    qty = int(item.quantity or 0)
                except Exception:
                    qty = 0

                try:
                    lt = float(item.line_total or 0.0)
                except Exception:
                    lt = 0.0

                total_items += max(0, qty)

                pid = int(item.product_id)
                if pid not in product_cache:
                    p = Product.objects(id=pid).first()
                    product_cache[pid] = p.name if p else f"Product #{pid}"
                product_name = product_cache.get(pid, f"Product #{pid}")

                unit_price = round((lt / qty), 2) if qty > 0 else 0.0

                sale_items_rows.append({
                    "sale_id": sale.id,
                    "sale_item_index": idx,
                    "created_at": created_at,
                    "retailer_id": rid,
                    "retailer_name": retailer_name,
                    "product_id": pid,
                    "product_name": product_name,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "line_total": round(lt, 2),
                })

        return {
            "sales": [sale.to_dict(include_items=True) for sale in sales],
            "sale_items": sale_items_rows,
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_transactions": sales.count(),
                "total_items_sold": total_items,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "retailer_id": retailer_id
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
                "retailer_id": user.id,
                "current_streak": 0,
                "daily_quota": 1000.0,
                "sales_today": 0.0,
                "total_sales": 0.0,
                "total_transactions": 0,
                "quota_progress": 0.0
            }

        quota_progress = (metrics.sales_today / metrics.daily_quota * 100) if metrics.daily_quota > 0 else 0

        return {
            "retailer_id": user.id,
            "current_streak": metrics.current_streak,
            "daily_quota": metrics.daily_quota,
            "sales_today": metrics.sales_today,
            "total_sales": metrics.total_sales,
            "total_transactions": metrics.total_transactions,
            "quota_progress": round(quota_progress, 2),
            "quota_met": metrics.sales_today >= metrics.daily_quota,
            "last_sale_date": metrics.last_sale_date.isoformat() if metrics.last_sale_date else None
        }

    @staticmethod
    def get_leaderboard(limit=10):
        """
        Get top-performing retailers by current streak and total sales.
        """
        top_metrics = (
            RetailerMetrics.objects(retailer__ne=None)
            .order_by("-current_streak", "-total_sales")
            .limit(int(limit))
        )

        leaderboard = []
        for idx, metrics in enumerate(top_metrics, 1):
            user = metrics.retailer
            leaderboard.append({
                "rank": idx,
                "retailer_id": user.id if user else None,
                "retailer_name": user.full_name if user else "Unknown",
                "current_streak": metrics.current_streak,
                "total_sales": metrics.total_sales,
                "sales_today": metrics.sales_today,
                "total_transactions": metrics.total_transactions
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
        metrics.daily_quota = float(new_quota)
        metrics.save()

        ActivityLogger.log_api_activity(
            method="PATCH",
            target_entity="retailer_metrics",
            user_id=int(retailer_id),
            details=f"Quota updated: ${old_quota:.2f} → ${float(new_quota):.2f}"
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
