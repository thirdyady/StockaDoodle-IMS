from mongoengine import StringField, DateTimeField, ReferenceField
from .base import BaseDocument
from .user import User
from datetime import datetime

class APIActivityLog(BaseDocument):
    meta = {
        'collection': 'api_activity_logs',
        'ordering': ['-timestamp']
        }
    
    # http method like POST or GET
    method = StringField(max_length=10, required=True)

    # the target entity name like product or user
    target_entity = StringField(max_length=50, required=True)

    # optional user responsible for the action
    user = ReferenceField(User, required=False)

    # where the action came from
    source = StringField(max_length=50, default="API")

    # details saved as text for flexible logging
    details = StringField()

    # when the action happened
    timestamp = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "method": self.method,
            "target": self.target_entity,
            "source": self.source,
            "user_id": self.user.id if self.user else None,
            "user_name": self.user.full_name if self.user else "System",
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
