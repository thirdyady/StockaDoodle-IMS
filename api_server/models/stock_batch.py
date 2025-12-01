from .base import BaseDocument
from mongoengine import IntField, DateField, DateTimeField, StringField, ReferenceField
from .user import User
from .product import Product
from datetime import datetime

class StockBatch(BaseDocument):
    meta = {
        'collection': 'stock_batches',
        'ordering': ['expiration_date']
        }

    # product this batch belongs to
    product = ReferenceField(Product)

    # how many items inside this batch
    quantity = IntField(required=True, default=0)

    # when this batch will expire
    expiration_date = DateField()

    # when this batch was added
    added_at = DateTimeField(default=datetime.utcnow)

    # optional: who added this stock
    added_by = ReferenceField(User)
    
    # reason for adding/removing stock
    reason = StringField(max_length=255)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id if self.product else None,
            "quantity": self.quantity,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "added_by": self.added_by.full_name if self.added_by else "Unknown",
            "reason": self.reason
        }
