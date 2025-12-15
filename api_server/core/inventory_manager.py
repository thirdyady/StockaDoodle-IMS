# api_server/core/inventory_manager.py

from models.product import Product
from models.stock_batch import StockBatch
from datetime import date
from typing import List, Dict


class InventoryError(Exception):
    """Custom exception for inventory issues."""
    pass


class InventoryManager:
    """
    Handles all inventory operations using FEFO (First Expired, First Out) principle.
    All stock deductions should go through this manager to ensure consistency.
    """

    # --------------------------------------------------------------
    # Get total stock level for a product
    # --------------------------------------------------------------
    @staticmethod
    def get_stock(product_id: int) -> int:
        """Return total available stock for a product by summing all batches."""
        product = Product.objects(id=product_id).first()
        if not product:
            raise InventoryError("Product not found")
        return product.stock_level

    # --------------------------------------------------------------
    # Validate that enough stock exists
    # --------------------------------------------------------------
    @staticmethod
    def validate_stock(product_id: int, qty_needed: int) -> bool:
        """Raise InventoryError if Deducting would cause insufficient stock."""
        product = Product.objects(id=product_id).first()
        if not product:
            raise InventoryError("Product not found")

        if product.stock_level < qty_needed:
            raise InventoryError(
                f"Not enough stock for '{product.name}': "
                f"needed {qty_needed}, available {product.stock_level}"
            )
        return True

    # --------------------------------------------------------------
    # Internal: FEFO sorting with NULL expiry last
    # --------------------------------------------------------------
    @staticmethod
    def _get_fefo_batches(product_id: int):
        """
        Returns batches sorted FEFO-style:
        1) Earliest expiration_date first
        2) expiration_date=None last
        3) Oldest added_at first for tie-break
        """
        batches = list(StockBatch.objects(product_id=product_id))

        def sort_key(b):
            exp = b.expiration_date
            # (is_no_expiry, exp_date_or_max, added_at_or_min)
            # is_no_expiry: False for real expiry, True for None -> so None goes last
            return (
                exp is None,
                exp or date.max,
                b.added_at or date.min
            )

        batches.sort(key=sort_key)
        return batches

    # --------------------------------------------------------------
    # Deduct stock FEFO-style (✅ now returns batch deductions)
    # --------------------------------------------------------------
    @staticmethod
    def deduct_stock_fefo(
        product_id: int,
        qty_needed: int,
        user_id: int = None,
        reason: str = None
    ) -> List[Dict[str, int]]:
        """
        Deduct stock from batches based on earliest expiration date first.
        Batches with NULL expiration are deducted last.

        ✅ Returns a list of deductions:
            [{"batch_id": <int>, "quantity": <int>}, ...]
        """
        product = Product.objects(id=product_id).first()
        if not product:
            raise InventoryError("Product not found")

        batches = InventoryManager._get_fefo_batches(product_id)

        remaining = int(qty_needed)
        deductions: List[Dict[str, int]] = []

        for batch in batches:
            if remaining <= 0:
                break
            if not batch.quantity or batch.quantity <= 0:
                continue

            deduct_qty = min(int(batch.quantity), remaining)

            batch.quantity = int(batch.quantity) - int(deduct_qty)
            remaining -= int(deduct_qty)
            batch.reason = reason or batch.reason
            batch.save()

            deductions.append({
                "batch_id": int(batch.id),
                "quantity": int(deduct_qty),
            })

        if remaining > 0:
            raise InventoryError(
                f"FEFO deduction failed — insufficient stock for product '{product.name}'"
            )

        return deductions

    # --------------------------------------------------------------
    # Deduct multiple products at once (e.g., during checkout)
    # --------------------------------------------------------------
    @staticmethod
    def apply_multi_fefo(items: list) -> bool:
        """
        Deduct multiple products at once using FEFO logic.
        Each item in 'items' must be a dict with 'product_id' and 'quantity'.
        """
        for entry in items:
            InventoryManager.validate_stock(entry["product_id"], entry["quantity"])

        for entry in items:
            # ignore the returned deductions here
            InventoryManager.deduct_stock_fefo(entry["product_id"], entry["quantity"])

        return True

    @staticmethod
    def get_low_stock_products(threshold_multiplier=1.0):
        from models.product import Product
        all_products = Product.objects()
        low_stock = []

        for product in all_products:
            threshold = product.min_stock_level * threshold_multiplier
            if product.stock_level < threshold:
                low_stock.append(product)

        return low_stock

    @staticmethod
    def get_expiring_batches(days_ahead=7):
        from datetime import timedelta
        cutoff_date = date.today() + timedelta(days=days_ahead)

        batches = StockBatch.objects(
            expiration_date__lte=cutoff_date,
            expiration_date__ne=None,
            quantity__gt=0
        )

        return list(batches)
