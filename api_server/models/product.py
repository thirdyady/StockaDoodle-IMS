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

    # link to a category
    category_id = IntField(required=True)
    
    # lowest allowed stock before warning
    min_stock_level = IntField(default=10)

    # this stores the product picture
    product_image = BinaryField()
    
    # longer description of the product, optional
    details = StringField(max_length=250)

    @property
    def stock_level(self):
        from .stock_batch import StockBatch
        # this adds all batch quantities together
        return sum((batch.quantity or 0) for batch in StockBatch.objects(product_id=self.id))
    
    @property
    def category(self):
        from .category import Category
        return Category.objects(id=self.category_id).first()

    def to_dict(self, include_image=False, include_batches=False):
        data = {
            "id": self.id,
            "name": self.name,
            "brand": self.brand or "",
            "price": self.price,
            "category": self.category.name if self.category else None,
            "stock_level": self.stock_level,
            "min_stock_level": self.min_stock_level,
            "details": self.details or "",
            "has_image": bool(self.product_image)
        }

        if include_image and self.product_image:
            # send image as binary data
            data["image_data"] = self.product_image

        if include_batches:
            from .stock_batch import StockBatch
            # include the list of all stock batches
            data["batches"] = [batch.to_dict() for batch in StockBatch.objects(product_id=self.id)]

        return data
