# api_server/models/product.py

import base64
from .base import BaseDocument
from mongoengine import StringField, IntField, BinaryField


class Product(BaseDocument):
    meta = {
        'collection': 'products',
        'ordering': ['name']
    }

    # name of the product, must be unique
    name = StringField(max_length=120, unique=True, required=True)

    # simple brand text
    brand = StringField(max_length=50)

    # price as whole number
    price = IntField(required=True)

    # link to a category (NOW OPTIONAL to match routes + UI)
    category_id = IntField(required=False, null=True)

    # lowest allowed stock before warning
    min_stock_level = IntField(default=10)

    # this stores the product picture
    product_image = BinaryField()

    # longer description of the product, optional
    details = StringField(max_length=250)

    @property
    def stock_level(self):
        """
        Computed from StockBatch documents.
        This is your real source of truth for inventory.
        """
        from .stock_batch import StockBatch
        batches = StockBatch.objects(product_id=self.id)
        total = 0
        for batch in batches:
            try:
                total += int(batch.quantity or 0)
            except Exception:
                total += 0
        return total

    @property
    def category(self):
        from .category import Category
        return Category.objects(id=self.category_id).first() if self.category_id else None

    def to_dict(self, include_image=False, include_batches=False):
        category_obj = self.category

        data = {
            "id": self.id,
            "name": self.name,
            "brand": self.brand or "",
            "price": self.price,

            # keep both for UI safety
            "category_id": self.category_id,
            "category": category_obj.name if category_obj else None,

            # explicit alias for clarity (non-breaking)
            "category_name": category_obj.name if category_obj else None,

            "stock_level": self.stock_level,
            "min_stock_level": self.min_stock_level,
            "details": self.details or "",
            "has_image": bool(self.product_image)
        }

        if include_image and self.product_image:
            data["image_data"] = base64.b64encode(self.product_image).decode('utf-8')
 
            data["image_data"] = self.product_image

        if include_batches:
            from .stock_batch import StockBatch
            # predictable order: exp earliest first, then added_at, then id
            batches = (
                StockBatch.objects(product_id=self.id)
                .order_by("expiration_date", "added_at")
            )
            data["batches"] = [batch.to_dict() for batch in batches]

        return data
