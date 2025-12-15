# api_server/models/stock_batch.py

from .base import BaseDocument
from mongoengine import IntField, DateField, DateTimeField, StringField, ReferenceField
from .user import User
from datetime import datetime, timezone


class StockBatch(BaseDocument):
    meta = {
        'collection': 'stock_batches',
        # Keep ordering, but FEFO manager should still override with safer logic
        'ordering': ['expiration_date']
    }

    # product this batch belongs to
    product_id = IntField(required=True)

    # how many items inside this batch
    quantity = IntField(required=True, default=0)

    # when this batch will expire
    expiration_date = DateField()

    # when this batch was added
    added_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    # optional: who added this stock
    added_by = ReferenceField(User)

    # reason for adding/removing stock
    reason = StringField(max_length=255)

    def to_dict(self):
        added_by_name = self.added_by.full_name if self.added_by else "Unknown"
        added_by_id = self.added_by.id if self.added_by else None

        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "added_at": self.added_at.isoformat() if self.added_at else None,

            # Backward + forward friendly
            "added_by": added_by_name,          # legacy name field
            "added_by_name": added_by_name,     # explicit
            "added_by_id": added_by_id,         # explicit id

            "reason": self.reason
        }
