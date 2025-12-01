from .base import BaseDocument
from mongoengine import (
    IntField,
    FloatField,
    DateTimeField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField
)
from datetime import datetime, timezone

class SaleItem(EmbeddedDocument):
    __tablename__ = "sale_items"
    product_id = IntField(required=True)

    # how many of that item
    quantity = IntField(default=0)

    # price * qty for that item
    line_total = FloatField(default=0.0)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "quantity": self.quantity,
            "line_total": self.line_total
        }
        
        
class Sale(BaseDocument):
    meta = {
        'collection': 'sales',
        'ordering': ['-created_at']
    }
    
    # which retailer made the sale
    retailer_id = IntField(required=True)
    
    # when the sale happened
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utcnow))
    
    # full sale amount
    total_amount = FloatField(default=0.0)
    
    # list of items inside this sale
    items = ListField(EmbeddedDocumentField(SaleItem))

    def to_dict(self, include_items=False):
        data = {
            "id": self.id,
            "user_id": self.retailer_id,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat(),
        }

        if include_items:
            # include every sale item if asked
            data["items"] = [item.to_dict() for item in self.items]

        return data


