from .base import BaseDocument
from mongoengine import IntField, StringField, DateTimeField, ReferenceField
from .user import User
from datetime import datetime, timezone

class ProductLog(BaseDocument):
    meta = {
        'collection': 'product_logs',
        'ordering': ['-log_time']
    }

    # product related to the log
    product_id = IntField(required=True)
    
    # number of stock added
    quantity = IntField()

    # user who performed the action
    user = ReferenceField(User)

    # type of action performed
    action_type = StringField(max_length=50, required=True)

    # optional notes about the action
    notes = StringField()

    # timestamp when the log was created
    log_time = DateTimeField(
        default=lambda: datetime.now(timezone.utc),
        required=True
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'user_id': self.user.id if self.user else None,
            'user_name': self.user.full_name if self.user else "System",
            'action_type': self.action_type,
            'notes': self.notes,
            'log_time': self.log_time.isoformat()
        }
