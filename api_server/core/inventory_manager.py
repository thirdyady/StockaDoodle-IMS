from models.product import Product
from models.stock_batch import StockBatch

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
        """Raise InventoryError if stock is insufficient."""
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
    # Deduct stock FEFO-style
    # --------------------------------------------------------------
    @staticmethod
    def deduct_stock_fefo(product_id: int, qty_needed: int) -> bool:
        """
        Deduct stock from batches based on earliest expiration date first.
        Batches with NULL expiration are deducted last.
        """
        product = Product.objects(id=product_id).first()
        if not product:
            raise InventoryError("Product not found")

        # Sort batches: earliest expiration first, NULLs last, then oldest added first
        batches = (
            StockBatch.objects(product_id=product_id)
            .order_by("+expiration_date", "+added_at") # Use "+" for ascending (nulls last)
        )

        remaining = qty_needed

        for batch in batches:
            if remaining <= 0:
                break
            if batch.quantity == 0:
                continue

            deduct_qty = min(batch.quantity, remaining)
            batch.quantity -= deduct_qty
            remaining -= deduct_qty
            batch.save()

        if remaining > 0:
            raise InventoryError(
                f"FEFO deduction failed — insufficient stock for product '{product.name}'"
            )

        return True

    # --------------------------------------------------------------
    # Deduct multiple products at once (e.g., during checkout)
    # --------------------------------------------------------------
    @staticmethod
    def apply_multi_fefo(items: list) -> bool:
        """
        Deduct multiple products at once using FEFO logic.
        Each item in 'items' must be a dict with 'product_id' and 'quantity'.

        Example:
        items = [
            {"product_id": 1, "quantity": 3},
            {"product_id": 2, "quantity": 5},
        ]
        """
        # First, validate all items to prevent partial deductions
        for entry in items:
            InventoryManager.validate_stock(entry["product_id"], entry["quantity"])

        # Deduct each item
        for entry in items:
            InventoryManager.deduct_stock_fefo(entry["product_id"], entry["quantity"])

        return True
